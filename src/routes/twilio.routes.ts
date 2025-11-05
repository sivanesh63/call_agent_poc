import { Router, Request, Response } from 'express';
import twilio from 'twilio';
import { CallHandlerService } from '../services/call-handler.service';
import { config } from '../config';

const router = Router();
const callHandler = new CallHandlerService();
const VoiceResponse = twilio.twiml.VoiceResponse;

/**
 * Webhook endpoint for incoming calls
 * This is called by Twilio when a call is received
 */
router.post('/incoming-call', async (req: Request, res: Response) => {
  try {
    const { CallSid, From, To } = req.body;

    console.log(`[Twilio] Incoming call - SID: ${CallSid}, From: ${From}, To: ${To}`);

    // Initialize call session
    await callHandler.initializeCall(CallSid, From, To);

    // Create Ultravox call and get join URL
    const ultravoxJoinUrl = await callHandler.createUltravoxCall(CallSid);

    // Create TwiML response
    const twiml = new VoiceResponse();

    if (ultravoxJoinUrl) {
      // Connect to Ultravox using WebRTC or SIP
      // For this example, we'll use a simple approach with <Connect>
      twiml.say('Hello! Please wait while I connect you to our AI assistant.');

      // Note: Ultravox typically provides a WebSocket URL for real-time communication
      // You may need to use Twilio's <Connect><Stream> to forward audio to Ultravox
      const connect = twiml.connect();
      connect.stream({
        url: ultravoxJoinUrl.replace('https://', 'wss://').replace('http://', 'ws://'),
      });
    } else {
      // Fallback response
      twiml.say('Hello! Welcome to our voice assistant. How can I help you today?');
      twiml.gather({
        input: ['speech'],
        action: '/twilio/handle-speech',
        method: 'POST',
        speechTimeout: 'auto',
      });
    }

    res.type('text/xml');
    res.send(twiml.toString());
  } catch (error) {
    console.error('[Twilio] Error handling incoming call:', error);

    const twiml = new VoiceResponse();
    twiml.say('Sorry, we encountered an error. Please try again later.');
    twiml.hangup();

    res.type('text/xml');
    res.send(twiml.toString());
  }
});

/**
 * Webhook endpoint for handling speech input
 */
router.post('/handle-speech', async (req: Request, res: Response) => {
  try {
    const { CallSid, SpeechResult } = req.body;

    console.log(`[Twilio] Speech received - SID: ${CallSid}, Speech: ${SpeechResult}`);

    if (!SpeechResult) {
      const twiml = new VoiceResponse();
      twiml.say("I didn't catch that. Could you please repeat?");
      twiml.gather({
        input: ['speech'],
        action: '/twilio/handle-speech',
        method: 'POST',
        speechTimeout: 'auto',
      });

      res.type('text/xml');
      res.send(twiml.toString());
      return;
    }

    // Process speech using OpenAI
    const response = await callHandler.processUserSpeech(CallSid, SpeechResult);

    // Create TwiML response
    const twiml = new VoiceResponse();
    twiml.say(response);

    // Continue gathering speech
    twiml.gather({
      input: ['speech'],
      action: '/twilio/handle-speech',
      method: 'POST',
      speechTimeout: 'auto',
    });

    res.type('text/xml');
    res.send(twiml.toString());
  } catch (error) {
    console.error('[Twilio] Error handling speech:', error);

    const twiml = new VoiceResponse();
    twiml.say('Sorry, I encountered an error processing your request.');
    twiml.hangup();

    res.type('text/xml');
    res.send(twiml.toString());
  }
});

/**
 * Webhook endpoint for call status updates
 */
router.post('/call-status', async (req: Request, res: Response) => {
  try {
    const { CallSid, CallStatus } = req.body;

    console.log(`[Twilio] Call status update - SID: ${CallSid}, Status: ${CallStatus}`);

    if (CallStatus === 'completed' || CallStatus === 'failed' || CallStatus === 'no-answer') {
      await callHandler.endCall(CallSid);
    }

    res.sendStatus(200);
  } catch (error) {
    console.error('[Twilio] Error handling call status:', error);
    res.sendStatus(500);
  }
});

/**
 * Health check endpoint
 */
router.get('/health', (req: Request, res: Response) => {
  const activeCalls = callHandler.getActiveCalls();
  res.json({
    status: 'ok',
    activeCalls: activeCalls.length,
    timestamp: new Date().toISOString(),
  });
});

export default router;
