import forge from 'node-forge';

export const encryptWithPublicKey = (data: string, publicKeyPem: string): string => {
  try {
    console.log(publicKeyPem)
    const publicKey = forge.pki.publicKeyFromPem(publicKeyPem);
    
    const encrypted = publicKey.encrypt(data, 'RSA-OAEP');
    
    return forge.util.encode64(encrypted);
  } catch (error) {
    console.error('Encryption failed:', error);
    throw new Error('Failed to encrypt API key');
  }
};

export const getPublicKey = (): string | null => {
  const publicKey = import.meta.env.VITE_PUBLIC_KEY;
  
  if (!publicKey) {
    console.warn('VITE_PUBLIC_KEY not found in environment variables');
    return null;
  }
  
  return publicKey;
};

export const encryptApiKey = (apiKey: string): string => {
  if (!apiKey || apiKey.trim() === '') {
    return apiKey;
  }
  
  try {
    const publicKey = getPublicKey();
    
    if (!publicKey) {
      console.warn('No public key available, sending API key unencrypted');
      return apiKey;
    }
    
    return encryptWithPublicKey(apiKey, publicKey);
  } catch (error) {
    console.error('Failed to encrypt API key:', error);
    console.warn('Sending API key unencrypted due to encryption failure');
    return apiKey;
  }
};