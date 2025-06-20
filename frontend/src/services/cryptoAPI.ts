/**
 * Crypto API Service - Kết nối với FastAPI backend
 * Path: /d:/CS317/frontend/src/services/cryptoAPI.ts
 */

// Request/Response interfaces tương ứng với backend
interface AskRequest {
  question: string;
}

interface AskResponse {
  answer: string;
}

// API Configuration
const API_BASE_URL = 'http://localhost:8000';

/**
 * Gửi câu hỏi crypto tới RAG chatbot backend
 * @param question - Câu hỏi của user
 * @returns Promise<string> - Câu trả lời từ AI
 */
export async function askCryptoQuestion(question: string): Promise<string> {
  try {
    console.log(`[API] Sending question: ${question}`);
    
    const response = await fetch(`${API_BASE_URL}/ask`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ question } as AskRequest),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data: AskResponse = await response.json();
    console.log(`[API] Received answer: ${data.answer}`);
    
    return data.answer;
  } catch (error) {
    console.error('[API] Error calling crypto API:', error);
    
    // Fallback error message
    if (error instanceof TypeError) {
      throw new Error('Không thể kết nối tới server. Vui lòng kiểm tra backend đã chạy chưa.');
    }
    
    throw new Error(`Lỗi API: ${error instanceof Error ? error.message : 'Unknown error'}`);
  }
}

/**
 * Kiểm tra health của backend server
 * @returns Promise<boolean> - True nếu server đang hoạt động
 */
export async function checkBackendHealth(): Promise<boolean> {
  try {
    const response = await fetch(`${API_BASE_URL}/docs`, { method: 'HEAD' });
    return response.ok;
  } catch {
    return false;
  }
}
