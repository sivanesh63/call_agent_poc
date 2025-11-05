import express, { Express, Request, Response, NextFunction } from 'express';
import { config, validateConfig } from './config';
import twilioRoutes from './routes/twilio.routes';

// Validate environment variables
try {
  validateConfig();
  console.log('✓ Configuration validated successfully');
} catch (error) {
  console.error('✗ Configuration validation failed:', error);
  process.exit(1);
}

const app: Express = express();

// Middleware
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Request logging middleware
app.use((req: Request, res: Response, next: NextFunction) => {
  const timestamp = new Date().toISOString();
  console.log(`[${timestamp}] ${req.method} ${req.path}`);
  next();
});

// Routes
app.use('/twilio', twilioRoutes);

// Root endpoint
app.get('/', (req: Request, res: Response) => {
  res.json({
    name: 'Twilio Ultravox Call Agent',
    version: '1.0.0',
    description: 'AI-powered voice agent using Twilio, Ultravox, and OpenAI',
    endpoints: {
      health: '/twilio/health',
      incomingCall: '/twilio/incoming-call',
      handleSpeech: '/twilio/handle-speech',
      callStatus: '/twilio/call-status',
    },
  });
});

// Health check endpoint
app.get('/health', (req: Request, res: Response) => {
  res.json({
    status: 'healthy',
    timestamp: new Date().toISOString(),
    uptime: process.uptime(),
  });
});

// Error handling middleware
app.use((error: Error, req: Request, res: Response, next: NextFunction) => {
  console.error('Error:', error);
  res.status(500).json({
    error: 'Internal server error',
    message: error.message,
  });
});

// 404 handler
app.use((req: Request, res: Response) => {
  res.status(404).json({
    error: 'Not found',
    path: req.path,
  });
});

// Start server
const server = app.listen(config.port, config.host, () => {
  console.log('\n' + '='.repeat(60));
  console.log('🎙️  Twilio Ultravox Call Agent');
  console.log('='.repeat(60));
  console.log(`\n✓ Server running on http://${config.host}:${config.port}`);
  console.log(`✓ Public URL: ${config.publicUrl || 'Not configured'}`);
  console.log(`\n📞 Twilio Configuration:`);
  console.log(`   Phone Number: ${config.twilio.phoneNumber}`);
  console.log(`   Account SID: ${config.twilio.accountSid.substring(0, 10)}...`);
  console.log(`\n🤖 AI Services:`);
  console.log(`   OpenAI Model: ${config.openai.model}`);
  console.log(`   Ultravox API: ${config.ultravox.baseUrl}`);
  console.log(`\n📋 Webhook URLs (configure in Twilio):`);
  console.log(`   Incoming Call: ${config.publicUrl}/twilio/incoming-call`);
  console.log(`   Call Status:   ${config.publicUrl}/twilio/call-status`);
  console.log('\n' + '='.repeat(60) + '\n');
});

// Graceful shutdown
process.on('SIGTERM', () => {
  console.log('\nReceived SIGTERM signal. Shutting down gracefully...');
  server.close(() => {
    console.log('Server closed');
    process.exit(0);
  });
});

process.on('SIGINT', () => {
  console.log('\nReceived SIGINT signal. Shutting down gracefully...');
  server.close(() => {
    console.log('Server closed');
    process.exit(0);
  });
});

export default app;
