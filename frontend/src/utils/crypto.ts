import { sha256 } from 'js-sha256'

export function hashPassword(username: string, plainPassword: string): string {
  return sha256(username + 'my-intelligence' + plainPassword)
}
