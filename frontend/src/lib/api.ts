import axios from "axios";
import type { PipelineResponse, OutputConfig } from "../types";

const api = axios.create({
  baseURL: "/api",
});

export const getHealth = async () => {
  const response = await api.get("/health");
  return response.data;
};

export const getDefaultConfig = async (): Promise<OutputConfig> => {
  const response = await api.get("/config/default");
  return response.data;
};

export const getExampleConfig = async (): Promise<OutputConfig> => {
  const response = await api.get("/config/example");
  return response.data;
};

export const runPipeline = async (
  files: File[],
  config?: OutputConfig
): Promise<PipelineResponse> => {
  const formData = new FormData();
  
  files.forEach((file) => {
    formData.append("files", file);
  });

  if (config) {
    formData.append("config", JSON.stringify(config));
  }

  const response = await api.post<PipelineResponse>("/pipeline/run", formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
  });
  
  return response.data;
};

export const getLastResult = async (): Promise<PipelineResponse> => {
  const response = await api.get<PipelineResponse>("/pipeline/last-result");
  return response.data;
};

export const getPipelineStatus = async () => {
  const response = await api.get("/pipeline/status");
  return response.data;
};
