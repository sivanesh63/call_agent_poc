import axios, { AxiosInstance } from 'axios';
import { config } from '../config';

export interface UltravoxCall {
  callId: string;
  status: string;
  joinUrl?: string;
}

export interface UltravoxCallOptions {
  systemPrompt: string;
  firstSpeaker: 'agent' | 'user';
  voice?: string;
  temperature?: number;
  model?: string;
}

export class UltravoxService {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: config.ultravox.baseUrl,
      headers: {
        'Authorization': `Bearer ${config.ultravox.apiKey}`,
        'Content-Type': 'application/json',
      },
    });
  }

  /**
   * Create a new Ultravox call session
   */
  async createCall(options: UltravoxCallOptions): Promise<UltravoxCall> {
    try {
      const response = await this.client.post('/calls', {
        systemPrompt: options.systemPrompt,
        model: options.model || 'fixie-ai/ultravox',
        voice: options.voice || 'terrence',
        temperature: options.temperature ?? 0.7,
        firstSpeaker: options.firstSpeaker,
      });

      return {
        callId: response.data.callId,
        status: response.data.status,
        joinUrl: response.data.joinUrl,
      };
    } catch (error) {
      console.error('Error creating Ultravox call:', error);
      throw error;
    }
  }

  /**
   * Get call status
   */
  async getCallStatus(callId: string): Promise<UltravoxCall> {
    try {
      const response = await this.client.get(`/calls/${callId}`);
      return {
        callId: response.data.callId,
        status: response.data.status,
        joinUrl: response.data.joinUrl,
      };
    } catch (error) {
      console.error('Error getting call status:', error);
      throw error;
    }
  }

  /**
   * End an active call
   */
  async endCall(callId: string): Promise<void> {
    try {
      await this.client.post(`/calls/${callId}/end`);
    } catch (error) {
      console.error('Error ending call:', error);
      throw error;
    }
  }

  /**
   * Create a call with custom configuration for Twilio integration
   */
  async createCallForTwilio(systemPrompt: string): Promise<string> {
    try {
      const call = await this.createCall({
        systemPrompt,
        firstSpeaker: 'agent',
        voice: 'terrence',
        temperature: 0.7,
      });

      // Return the join URL that Twilio can connect to
      return call.joinUrl || '';
    } catch (error) {
      console.error('Error creating call for Twilio:', error);
      throw error;
    }
  }
}
