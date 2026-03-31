const PROD_API = "https://ai-logistics-system.onrender.com";
const LOCAL_API = "http://127.0.0.1:8002";

export const BASE_URL =
  process.env.REACT_APP_API_URL ||
  (process.env.NODE_ENV === "development" ? LOCAL_API : PROD_API);
