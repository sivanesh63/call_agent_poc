# Twilio Ultravox Call Agent

An AI-powered voice agent that receives phone calls through Twilio, processes them with Ultravox for real-time voice interaction, and uses OpenAI for intelligent responses.

## Features

- **Twilio Integration**: Receives and handles incoming phone calls
- **Ultravox Real-time Voice**: Provides natural, real-time voice interactions
- **OpenAI LLM**: Powers intelligent conversational responses
- **Call Session Management**: Tracks active calls and conversation history
- **WebSocket Support**: Real-time audio streaming with Ultravox
- **TypeScript**: Fully typed codebase for better development experience

## Architecture

```
Incoming Call (Twilio)
    ↓
Webhook Handler (Express)
    ↓
Call Handler Service
    ├── OpenAI Service (LLM Processing)
    └── Ultravox Service (Real-time Voice)
    ↓
Voice Response → Caller
```

## Prerequisites

Before you begin, ensure you have the following:

1. **Node.js** (v18 or higher)
2. **Twilio Account** with:
   - Account SID
   - Auth Token
   - A phone number
3. **OpenAI API Key**
4. **Ultravox API Key**
5. **Public URL** (for webhooks):
   - Use [ngrok](https://ngrok.com/) for local development
   - Or deploy to a cloud platform

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd call_agent_poc
```

2. Install dependencies:
```bash
npm install
```

3. Create environment file:
```bash
cp .env.example .env
```

4. Edit `.env` and fill in your credentials:
```env
# Server Configuration
PORT=3000
HOST=0.0.0.0

# Twilio Configuration
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_PHONE_NUMBER=your_twilio_phone_number

# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4-turbo-preview

# Ultravox Configuration
ULTRAVOX_API_KEY=your_ultravox_api_key
ULTRAVOX_BASE_URL=https://api.ultravox.ai

# Application Configuration
PUBLIC_URL=https://your-public-url.com
```

## Development

### Build the project:
```bash
npm run build
```

### Run in development mode:
```bash
npm run dev
```

### Run in production mode:
```bash
npm start
```

## Setting Up Ngrok (Local Development)

1. Install ngrok:
```bash
# Using npm
npm install -g ngrok

# Or download from https://ngrok.com/download
```

2. Start your server:
```bash
npm run dev
```

3. In a new terminal, start ngrok:
```bash
ngrok http 3000
```

4. Copy the ngrok URL (e.g., `https://abc123.ngrok.io`)

5. Update your `.env` file:
```env
PUBLIC_URL=https://abc123.ngrok.io
```

6. Restart your server

## Configuring Twilio

1. Log in to your [Twilio Console](https://console.twilio.com/)

2. Go to **Phone Numbers** → **Manage** → **Active numbers**

3. Click on your phone number

4. Scroll to **Voice Configuration**:
   - **A CALL COMES IN**: Webhook
   - URL: `https://your-public-url.com/twilio/incoming-call`
   - HTTP Method: `POST`

5. Under **Call Status Changes**:
   - URL: `https://your-public-url.com/twilio/call-status`
   - HTTP Method: `POST`

6. Click **Save**

## Testing the Agent

1. Ensure your server is running:
```bash
npm run dev
```

2. Check the health endpoint:
```bash
curl http://localhost:3000/health
```

3. Call your Twilio phone number from any phone

4. The agent should:
   - Answer the call
   - Greet you
   - Listen to your speech
   - Respond intelligently using OpenAI
   - Continue the conversation

## API Endpoints

### Root
- `GET /` - API information and available endpoints

### Health Check
- `GET /health` - Server health status
- `GET /twilio/health` - Twilio integration health with active calls count

### Twilio Webhooks
- `POST /twilio/incoming-call` - Handles incoming calls
- `POST /twilio/handle-speech` - Processes speech input
- `POST /twilio/call-status` - Receives call status updates

## Project Structure

```
call_agent_poc/
├── src/
│   ├── config.ts                      # Configuration management
│   ├── server.ts                      # Express server setup
│   ├── routes/
│   │   └── twilio.routes.ts          # Twilio webhook routes
│   └── services/
│       ├── openai.service.ts         # OpenAI integration
│       ├── ultravox.service.ts       # Ultravox integration
│       └── call-handler.service.ts   # Call session management
├── dist/                              # Compiled TypeScript output
├── .env                               # Environment variables (not in git)
├── .env.example                       # Environment template
├── package.json                       # Dependencies
├── tsconfig.json                      # TypeScript configuration
└── README.md                          # This file
```

## How It Works

1. **Call Received**: When someone calls your Twilio number, Twilio sends a webhook to `/twilio/incoming-call`

2. **Session Initialization**: The server creates a call session and initializes conversation tracking

3. **Ultravox Connection**: Creates an Ultravox call session for real-time voice processing

4. **Speech Processing**:
   - User speaks
   - Twilio converts speech to text
   - Text is sent to `/twilio/handle-speech`

5. **AI Response**:
   - OpenAI processes the user's message
   - Generates an intelligent response
   - Response is converted to speech and played to caller

6. **Conversation Loop**: Steps 4-5 repeat until the call ends

7. **Call End**: When the call ends, the session is cleaned up

## Customization

### Modify the AI Assistant Personality

Edit `src/services/openai.service.ts`, function `getSystemPrompt()`:

```typescript
getSystemPrompt(): string {
  return `You are a helpful customer service agent for ACME Corporation.
Your role is to assist customers with their orders and questions.
Be professional, friendly, and concise in your responses.`;
}
```

### Change Voice Settings

Edit `src/services/ultravox.service.ts`, in the `createCall` method:

```typescript
voice: 'terrence', // Change to different Ultravox voice
temperature: 0.7,  // Adjust creativity (0.0 - 1.0)
```

### Adjust OpenAI Model

Update `.env`:
```env
OPENAI_MODEL=gpt-4-turbo-preview  # or gpt-3.5-turbo for faster/cheaper
```

## Troubleshooting

### Call not connecting
- Verify your `PUBLIC_URL` is accessible from the internet
- Check Twilio webhook configuration
- Ensure ngrok is running (for local development)

### No AI responses
- Verify `OPENAI_API_KEY` is valid
- Check OpenAI API quota
- Review server logs for errors

### Ultravox connection issues
- Verify `ULTRAVOX_API_KEY` is valid
- Check Ultravox service status
- Review network connectivity

### View logs
```bash
# Development
npm run dev

# Production
npm start
```

## Security Considerations

- Never commit `.env` file to version control
- Use environment variables for all secrets
- Validate Twilio webhook signatures in production
- Implement rate limiting for production use
- Use HTTPS for all webhook endpoints

## Cost Considerations

- **Twilio**: ~$0.013/minute for voice calls
- **OpenAI**: Varies by model (GPT-4 is more expensive than GPT-3.5)
- **Ultravox**: Check Ultravox pricing
- Consider using GPT-3.5-turbo for development to reduce costs

## Deployment

### Deploy to Cloud Platform

The application can be deployed to:
- **Heroku**: `git push heroku main`
- **Railway**: Connect GitHub repo
- **Google Cloud Run**: Build container and deploy
- **AWS Elastic Beanstalk**: Deploy Node.js application

Remember to set environment variables on your platform!

## License

MIT

## Support

For issues and questions:
- Check the [Twilio documentation](https://www.twilio.com/docs)
- Review [OpenAI API docs](https://platform.openai.com/docs)
- Consult [Ultravox documentation](https://ultravox.ai/docs)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
