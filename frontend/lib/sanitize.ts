/**Client-side input sanitization utilities.*/

const EMAIL_PATTERN = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
const PHONE_PATTERN = /^\+?[\d\s\-()]{7,20}$/;

export function escapeHtml(text: string): string {
  const map: Record<string, string> = {
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#x27;',
  };
  return text.replace(/[&<>"']/g, (c) => map[c]);
}

export function sanitizeInput(input: string, maxLength: number = 1000): string {
  return escapeHtml(input.trim().slice(0, maxLength));
}

export function isValidEmail(value: string): boolean {
  return EMAIL_PATTERN.test(value);
}

export function isValidPhone(value: string): boolean {
  return PHONE_PATTERN.test(value);
}
