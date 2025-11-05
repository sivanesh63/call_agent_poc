import OpenAI from 'openai';
import { config } from '../config';

export class OpenAIService {
  private client: OpenAI;

  constructor() {
    this.client = new OpenAI({
      apiKey: config.openai.apiKey,
    });
  }

  /**
   * Generate a response using OpenAI's chat completion
   */
  async generateResponse(
    messages: Array<{ role: 'system' | 'user' | 'assistant'; content: string }>,
    options?: {
      temperature?: number;
      maxTokens?: number;
      stream?: boolean;
    }
  ): Promise<string> {
    try {
      const response = await this.client.chat.completions.create({
        model: config.openai.model,
        messages,
        temperature: options?.temperature ?? 0.7,
        max_tokens: options?.maxTokens ?? 500,
        stream: false,
      });

      return response.choices[0]?.message?.content || '';
    } catch (error) {
      console.error('Error generating OpenAI response:', error);
      throw error;
    }
  }

  /**
   * Generate a streaming response using OpenAI's chat completion
   */
  async *generateStreamingResponse(
    messages: Array<{ role: 'system' | 'user' | 'assistant'; content: string }>,
    options?: {
      temperature?: number;
      maxTokens?: number;
    }
  ): AsyncGenerator<string, void, unknown> {
    try {
      const stream = await this.client.chat.completions.create({
        model: config.openai.model,
        messages,
        temperature: options?.temperature ?? 0.7,
        max_tokens: options?.maxTokens ?? 500,
        stream: true,
      });

      for await (const chunk of stream) {
        const content = chunk.choices[0]?.delta?.content;
        if (content) {
          yield content;
        }
      }
    } catch (error) {
      console.error('Error generating streaming OpenAI response:', error);
      throw error;
    }
  }

  /**
   * Create a system prompt for the voice agent
   */
  getSystemPrompt(): string {
    return `You are a helpful voice assistant. You are receiving phone calls and need to respond naturally and conversationally.
Your responses should be:
- Concise and clear (suitable for voice conversation)
- Natural and friendly
- Helpful and informative
- Limited to 2-3 sentences per response to keep the conversation flowing

When users call, greet them warmly and ask how you can help them today.`;
  }
}
