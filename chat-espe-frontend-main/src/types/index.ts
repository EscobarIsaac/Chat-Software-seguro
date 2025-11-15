export interface Message {
  msg?: string;
  username: string;
  timestamp: string;
  type: 'text' | 'file';
  filename?: string;
  filetype?: string;
  file?: string;
}

export interface RoomForm {
  name: string;
  pin: string;
  type: 'text' | 'multimedia';
}