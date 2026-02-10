// API client for Aethel backend

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface VerifyRequest {
  code: string;
}

export interface VerifyResponse {
  status: 'PROVED' | 'FAILED' | 'ERROR';
  message: string;
  proof?: any;
  audit_trail?: string[];
}

export interface Example {
  name: string;
  code: string;
  description: string;
}

export async function verifyCode(code: string): Promise<VerifyResponse> {
  try {
    const response = await fetch(`${API_URL}/api/verify`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ code }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Verification error:', error);
    return {
      status: 'ERROR',
      message: error instanceof Error ? error.message : 'Unknown error occurred',
    };
  }
}

export async function getExamples(): Promise<Example[]> {
  try {
    // Add cache-busting timestamp to force fresh data
    const timestamp = new Date().getTime();
    const response = await fetch(`${API_URL}/api/examples?_t=${timestamp}`, {
      cache: 'no-store', // Disable caching
      headers: {
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache'
      }
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    console.log('✅ Fetched examples from backend:', data.examples?.length || 0);
    // API returns { success: true, examples: [...], count: 3 }
    return data.examples || [];
  } catch (error) {
    console.error('❌ Failed to fetch examples:', error);
    return [];
  }
}

export async function compileCode(code: string): Promise<any> {
  try {
    const response = await fetch(`${API_URL}/api/compile`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ code }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Compilation error:', error);
    throw error;
  }
}
