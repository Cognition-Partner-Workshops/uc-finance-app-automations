import { io } from 'socket.io-client';
import { Environment } from './env';

const URL = process.env.NODE_ENV === 'production' ? undefined : Environment.trade_feed_url;

export const socket = io(URL || '');
