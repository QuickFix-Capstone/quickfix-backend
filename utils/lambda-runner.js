import { spawn } from 'child_process';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

/**
 * Convert Express request to AWS Lambda event format
 */
function expressToLambdaEvent(req, pathParams = {}) {
    const event = {
        httpMethod: req.method,
        path: req.path,
        pathParameters: pathParams,
        headers: {},
        body: null,
        isBase64Encoded: false,
        requestContext: {
            authorizer: {
                jwt: {
                    claims: {}
                }
            }
        }
    };

    // Convert headers (lowercase keys for consistency)
    for (const [key, value] of Object.entries(req.headers)) {
        event.headers[key.toLowerCase()] = value;
    }

    // Handle body
    if (req.body) {
        if (Buffer.isBuffer(req.body)) {
            // Raw body (for webhooks)
            event.body = req.body.toString('utf8');
        } else if (typeof req.body === 'object') {
            event.body = JSON.stringify(req.body);
        } else {
            event.body = String(req.body);
        }
    }

    // Extract JWT from Authorization header for local testing
    const authHeader = req.headers.authorization || req.headers.Authorization;
    if (authHeader && authHeader.startsWith('Bearer ')) {
        // In real AWS, this would be parsed by API Gateway
        // For local dev, we just pass it through and rely on DEV_COGNITO_SUB fallback
        event.requestContext.authorizer.jwt.claims.sub = process.env.DEV_COGNITO_SUB || 'local-test-user';
    }

    return event;
}

/**
 * Execute a Python Lambda function handler
 * @param {string} lambdaDir - Directory name of the lambda function (e.g., 'payment_quote')
 * @param {object} event - Lambda event object
 * @param {number} timeout - Timeout in milliseconds (default: 30000)
 * @returns {Promise<object>} Lambda response object
 */
export async function invokeLambda(lambdaDir, event, timeout = 30000) {
    return new Promise((resolve, reject) => {
        const lambdaPath = path.join(__dirname, '..', 'lambda', lambdaDir);
        const runLocalPath = path.join(lambdaPath, 'run_local.py');

        const python = spawn('python', [runLocalPath], {
            cwd: lambdaPath,
            env: { ...process.env },
            timeout
        });

        let stdout = '';
        let stderr = '';

        python.stdout.on('data', (data) => {
            stdout += data.toString();
        });

        python.stderr.on('data', (data) => {
            stderr += data.toString();
        });

        // Send event to stdin
        python.stdin.write(JSON.stringify(event));
        python.stdin.end();

        python.on('close', (code) => {
            if (code !== 0) {
                console.error(`Lambda ${lambdaDir} failed with code ${code}`);
                console.error('STDERR:', stderr);
                return reject(new Error(`Lambda execution failed: ${stderr || 'Unknown error'}`));
            }

            try {
                // Parse Lambda response from stdout
                const response = JSON.parse(stdout);
                resolve(response);
            } catch (err) {
                console.error(`Failed to parse Lambda response from ${lambdaDir}`);
                console.error('STDOUT:', stdout);
                console.error('STDERR:', stderr);
                reject(new Error(`Failed to parse Lambda response: ${err.message}`));
            }
        });

        python.on('error', (err) => {
            reject(new Error(`Failed to spawn Python process: ${err.message}`));
        });

        // Handle timeout
        setTimeout(() => {
            python.kill();
            reject(new Error(`Lambda execution timeout after ${timeout}ms`));
        }, timeout);
    });
}

/**
 * Execute Lambda and send response to Express
 */
export async function handleLambdaRequest(req, res, lambdaDir, pathParams = {}) {
    try {
        const event = expressToLambdaEvent(req, pathParams);
        const lambdaResponse = await invokeLambda(lambdaDir, event);

        // Extract status code, headers, and body from Lambda response
        const statusCode = lambdaResponse.statusCode || 200;
        const headers = lambdaResponse.headers || {};
        let body = lambdaResponse.body;

        // Parse body if it's a JSON string
        if (typeof body === 'string') {
            try {
                body = JSON.parse(body);
            } catch (e) {
                // Keep as string if not valid JSON
            }
        }

        // Set response headers
        for (const [key, value] of Object.entries(headers)) {
            res.setHeader(key, value);
        }

        // Send response
        res.status(statusCode).json(body);
    } catch (error) {
        console.error(`Error handling Lambda request for ${lambdaDir}:`, error);
        res.status(500).json({
            error: 'Internal server error',
            details: error.message
        });
    }
}
