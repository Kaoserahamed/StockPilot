'use client';
import { useState, useCallback } from 'react';

type ValidationRule = {
  required?: boolean;
  minLength?: number;
  maxLength?: number;
  pattern?: RegExp;
  message?: string;
};

type FieldRules = Record<string, ValidationRule>;
type FieldErrors = Record<string, string>;

/**
 * Hook for form validation with real-time feedback.
 *
 * @param rules - Validation rules for each field
 *
 * Usage:
 *   const { errors, validate, validateField, clearErrors } = useFormValidation({
 *     email: { required: true, pattern: /^[^\s@]+@[^\s@]+\.[^\s@]+$/, message: 'Invalid email' },
 *     password: { required: true, minLength: 8, message: 'Min 8 characters' },
 *   });
 */
export function useFormValidation(rules: FieldRules) {
  const [errors, setErrors] = useState<FieldErrors>({});

  const validateField = useCallback((name: string, value: string): string => {
    const rule = rules[name];
    if (!rule) return '';

    if (rule.required && (!value || value.trim() === '')) {
      return rule.message || `${name} is required`;
    }
    if (rule.minLength && value.length < rule.minLength) {
      return rule.message || `${name} must be at least ${rule.minLength} characters`;
    }
    if (rule.maxLength && value.length > rule.maxLength) {
      return rule.message || `${name} must be at most ${rule.maxLength} characters`;
    }
    if (rule.pattern && !rule.pattern.test(value)) {
      return rule.message || `${name} is invalid`;
    }
    return '';
  }, [rules]);

  const validate = useCallback((data: Record<string, string>): boolean => {
    const newErrors: FieldErrors = {};
    let isValid = true;

    for (const [name, rule] of Object.entries(rules)) {
      const error = validateField(name, data[name] || '');
      if (error) {
        newErrors[name] = error;
        isValid = false;
      }
    }

    setErrors(newErrors);
    return isValid;
  }, [rules, validateField]);

  const validateSingle = useCallback((name: string, value: string) => {
    const error = validateField(name, value);
    setErrors((prev) => {
      if (error) return { ...prev, [name]: error };
      const { [name]: _, ...rest } = prev;
      return rest;
    });
    return error;
  }, [validateField]);

  const clearErrors = useCallback(() => setErrors({}), []);
  const clearFieldError = useCallback((name: string) => {
    setErrors((prev) => {
      const { [name]: _, ...rest } = prev;
      return rest;
    });
  }, []);

  return { errors, validate, validateField: validateSingle, clearErrors, clearFieldError };
}
