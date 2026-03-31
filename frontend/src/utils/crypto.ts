export async function hashPassword(username: string, plainPassword: string): Promise<string> {
  const raw = username + 'my-intelligence' + plainPassword
  const encoded = new TextEncoder().encode(raw)
  const buffer = await crypto.subtle.digest('SHA-256', encoded)
  const bytes = new Uint8Array(buffer)
  return Array.from(bytes)
    .map((b) => b.toString(16).padStart(2, '0'))
    .join('')
}
