export type RelayQrPayload = {
  v: number;
  mode: string;
  ws: string;
  pair: string;
};

export type RelayPairCreateResponse = {
  pair_id: string;
  pair_token: string;
  agent_token: string;
  relay_ws_url: string;
  relay_agent_url: string;
  expires_at: string;
  qr_payload: RelayQrPayload;
};

export type RelayPairRead = {
  pair_id: string;
  device_name: string | null;
  expires_at: string;
  revoked_at: string | null;
  created_at: string;
  pc_online: boolean;
  phone_connections: number;
};

export type RelayPairListResponse = {
  items: RelayPairRead[];
};

export type RelayPairStatusResponse = {
  pair_id: string;
  pc_online: boolean;
  phone_connections: number;
  last_agent_seen_at: string | null;
};

export type RelayMessageRead = {
  id: string;
  pair_id: string;
  text: string;
  mode: string | null;
  after_key: string | null;
  smart_mode: boolean;
  smart_action: string | null;
  delivery_status: string;
  ack_ok: boolean | null;
  ack_error: string | null;
  client_ip: string | null;
  created_at: string;
};

export type RelayMessageListResponse = {
  total: number;
  page: number;
  page_size: number;
  items: RelayMessageRead[];
};

export type RelayMessageStatsResponse = {
  total: number;
  today: number;
  delivered: number;
  pc_offline: number;
};

export type RelayPairRefreshResponse = {
  pair_token: string;
  expires_at: string;
  qr_payload: RelayQrPayload;
};
