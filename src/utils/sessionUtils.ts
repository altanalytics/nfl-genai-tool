// Generate a 33-character session ID with userName as prefix (spaces stripped)
export const generateSessionId = (userName: string): string => {
  const chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
  
  // Strip spaces from userName and use as prefix, truncate if too long
  const cleanUserName = userName.replace(/\s+/g, '');
  const prefix = cleanUserName.substring(0, Math.min(cleanUserName.length, 20));
  const remainingLength = 33 - prefix.length;
  
  let randomSuffix = '';
  for (let i = 0; i < remainingLength; i++) {
    randomSuffix += chars.charAt(Math.floor(Math.random() * chars.length));
  }
  
  const sessionId = prefix + randomSuffix;
  
  // Ensure exactly 33 characters
  if (sessionId.length !== 33) {
    console.warn(`Session ID length is ${sessionId.length}, expected 33. Adjusting...`);
    if (sessionId.length < 33) {
      // Pad with random characters
      const padding = 33 - sessionId.length;
      for (let i = 0; i < padding; i++) {
        sessionId += chars.charAt(Math.floor(Math.random() * chars.length));
      }
    } else {
      // Truncate to 33 characters
      return sessionId.substring(0, 33);
    }
  }
  
  return sessionId;
};

export const formatTime = (date: Date): string => {
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
};
