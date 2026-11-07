import type { Transport } from "./api";
// The real build must not ship mock question answers alongside the API client.
export const mockTransport: Transport = async () => {
  throw new Error("Mock transport is only available with VITE_MOCK=1.");
};
