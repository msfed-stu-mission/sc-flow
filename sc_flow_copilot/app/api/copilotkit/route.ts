import {
  CopilotRuntime,
  OpenAIAdapter,
  EmptyAdapter,
  copilotRuntimeNextJSAppRouterEndpoint,
} from '@copilotkit/runtime';
import OpenAI from 'openai';
import { NextRequest } from 'next/server';


const serviceAdapter = (() => {
  try{
    const apiKey = process.env.AZURE_OPENAI_API_KEY;
    const baseURL = process.env.AZURE_OPENAI_ENDPOINT;
    const deployment = process.env.LLM_DEPLOYMENT_NAME;
    const apiVersion = process.env.OPENAI_API_VERSION;
    const openai =new OpenAI({
      apiKey: apiKey,
      baseURL: `${baseURL}/openai/deployments/${deployment}`,
      defaultQuery: { "api-version": apiVersion },
      defaultHeaders: { "api-key": apiKey },
    }); 
    return new OpenAIAdapter({ openai });
  } catch(error) {
    console.log("Using an empty LLM adapter, some functionality won't be available")
    return new EmptyAdapter();
  } 
})();

const server_endpoint_url = `${process.env.SERVER_ENDPOINT_URL}/${process.env.SERVER_SCFLOW_PATH}`;
const runtime = new CopilotRuntime({
  remoteEndpoints: [ 
      { url: server_endpoint_url },
  ],
}); 
export const POST = async (req: NextRequest) => {
  const { handleRequest } = copilotRuntimeNextJSAppRouterEndpoint({
    runtime,
    serviceAdapter,
    endpoint: '/api/copilotkit',
  });
 
  return handleRequest(req);
};