import {
  BatchSpanProcessor,
  WebTracerProvider,
} from "@opentelemetry/sdk-trace-web";
import { Resource } from "@opentelemetry/resources";
import {
  SEMRESATTRS_SERVICE_NAME,
  SEMRESATTRS_SERVICE_VERSION,
} from "@opentelemetry/semantic-conventions";
import { ZoneContextManager } from "@opentelemetry/context-zone";
import { W3CTraceContextPropagator } from "@opentelemetry/core";
import { registerInstrumentations } from "@opentelemetry/instrumentation";
import { OTLPTraceExporter } from "@opentelemetry/exporter-trace-otlp-proto";
import { getWebAutoInstrumentations } from "@opentelemetry/auto-instrumentations-web";
import { getServerUrl } from "./api/getServerUrl";

const resource = Resource.default().merge(
  new Resource({
    [SEMRESATTRS_SERVICE_NAME]: "automatic-data-analyzer-frontend",
    [SEMRESATTRS_SERVICE_VERSION]: "0.1.0",
  })
);
const provider = new WebTracerProvider({ resource });

const otlpExporter = new OTLPTraceExporter({
  // url: "http://localhost:4318/v1/traces",
});
provider.addSpanProcessor(new BatchSpanProcessor(otlpExporter));

provider.register({
  // Changing default contextManager to use ZoneContextManager - supports asynchronous operations - optional
  contextManager: new ZoneContextManager(),
  propagator: new W3CTraceContextPropagator(),
});

// Registering instrumentations
registerInstrumentations({
  instrumentations: [
    getWebAutoInstrumentations({
      "@opentelemetry/instrumentation-fetch": {
        propagateTraceHeaderCorsUrls: [new RegExp(getServerUrl())],
      },
      "@opentelemetry/instrumentation-xml-http-request": {
        enabled: false,
      },
    }),
  ],
});
