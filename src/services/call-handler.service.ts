import { OpenAIService } from './openai.service';
import { UltravoxService } from './ultravox.service';

export interface CallSession {
  callSid: string;
  from: string;
  to: string;
  startTime: Date;
  ultravoxCallId?: string;
  conversationHistory: Array<{
    role: 'system' | 'user' | 'assistant';
    content: string;
  }>;
}

export class CallHandlerService {
  private openaiService: OpenAIService;
  private ultravoxService: UltravoxService;
  private activeCalls: Map<string, CallSession>;

  constructor() {
    this.openaiService = new OpenAIService();
    this.ultravoxService = new UltravoxService();
    this.activeCalls = new Map();
  }

  /**
   * Initialize a new call session
   */
  async initializeCall(callSid: string, from: string, to: string): Promise<CallSession> {
    const session: CallSession = {
      callSid,
      from,
      to,
      startTime: new Date(),
      conversationHistory: [
        {
          role: 'system',
          content: this.openaiService.getSystemPrompt(),
        },
      ],
    };

    this.activeCalls.set(callSid, session);
    console.log(`[Call Handler] Initialized call session: ${callSid} from ${from} to ${to}`);

    return session;
  }

  /**
   * Create Ultravox call with OpenAI-powered system prompt
   */
  async createUltravoxCall(callSid: string): Promise<string> {
    const session = this.activeCalls.get(callSid);
    if (!session) {
      throw new Error(`Call session not found: ${callSid}`);
    }

    try {
      // Create an enhanced system prompt using OpenAI
      const systemPrompt = this.openaiService.getSystemPrompt();

      // Create Ultravox call
      const joinUrl = await this.ultravoxService.createCallForTwilio(systemPrompt);

      // Store the Ultravox call ID
      session.ultravoxCallId = joinUrl;
      this.activeCalls.set(callSid, session);

      console.log(`[Call Handler] Created Ultravox call for session: ${callSid}`);
      return joinUrl;
    } catch (error) {
      console.error(`[Call Handler] Error creating Ultravox call:`, error);
      throw error;
    }
  }

  /**
   * Process user speech and generate response
   */
  async processUserSpeech(callSid: string, userMessage: string): Promise<string> {
    const session = this.activeCalls.get(callSid);
    if (!session) {
      throw new Error(`Call session not found: ${callSid}`);
    }

    try {
      // Add user message to conversation history
      session.conversationHistory.push({
        role: 'user',
        content: userMessage,
      });

      // Generate response using OpenAI
      const response = await this.openaiService.generateResponse(
        session.conversationHistory,
        { temperature: 0.7, maxTokens: 150 }
      );

      // Add assistant response to conversation history
      session.conversationHistory.push({
        role: 'assistant',
        content: response,
      });

      this.activeCalls.set(callSid, session);

      console.log(`[Call Handler] Generated response for call ${callSid}`);
      return response;
    } catch (error) {
      console.error(`[Call Handler] Error processing speech:`, error);
      throw error;
    }
  }

  /**
   * End a call session
   */
  async endCall(callSid: string): Promise<void> {
    const session = this.activeCalls.get(callSid);
    if (!session) {
      console.warn(`[Call Handler] Call session not found: ${callSid}`);
      return;
    }

    try {
      // End Ultravox call if exists
      if (session.ultravoxCallId) {
        // Extract call ID from join URL if needed
        // await this.ultravoxService.endCall(session.ultravoxCallId);
      }

      this.activeCalls.delete(callSid);
      console.log(`[Call Handler] Ended call session: ${callSid}`);
    } catch (error) {
      console.error(`[Call Handler] Error ending call:`, error);
      throw error;
    }
  }

  /**
   * Get call session
   */
  getCallSession(callSid: string): CallSession | undefined {
    return this.activeCalls.get(callSid);
  }

  /**
   * Get all active calls
   */
  getActiveCalls(): CallSession[] {
    return Array.from(this.activeCalls.values());
  }
}
