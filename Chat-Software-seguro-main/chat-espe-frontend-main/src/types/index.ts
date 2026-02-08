// Define el tipo de un mensaje
export type Message = {
  type: 'text' | 'file';
  username: string;
  timestamp: string;
  msg?: string;          // Para mensajes de texto
  file?: string;         // Base64 del archivo
  filename?: string;
  filetype?: string;
  isAdmin?: boolean;     // Indica si el mensaje es de un admin
};

// Define el formulario de creación de sala
// 'type' es opcional ya que lo quitamos del formulario
export type RoomForm = {
  name: string;
  pin: string;
  type?: 'text' | 'multimedia';
};