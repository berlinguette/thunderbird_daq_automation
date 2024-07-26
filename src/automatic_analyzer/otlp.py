from opentelemetry._logs import set_logger_provider
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
# from opentelemetry.sdk.resources import Resource, SERVICE_NAME

# from opentelemetry import trace
# from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
# from opentelemetry.sdk.trace import TracerProvider
# from opentelemetry.sdk.trace.export import BatchSpanProcessor

# from opentelemetry import metrics
# from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
# from opentelemetry.sdk.metrics import MeterProvider
# from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader

def get_otlp_log_handler():
    # Create and set the logger provider
    logger_provider = LoggerProvider()
    set_logger_provider(logger_provider)

    # Create the OTLP log exporter that sends logs to configured destination
    exporter = OTLPLogExporter()
    logger_provider.add_log_record_processor(BatchLogRecordProcessor(exporter))

    # Attach OTLP handler to root logger
    handler = LoggingHandler(logger_provider=logger_provider)

    return handler

# Ensure the logger is shutdown before exiting so all pending logs are exported
# logger_provider.shutdown()

# Service name is required for most backends
# resource = Resource(attributes={
#     SERVICE_NAME: "automatic-data-analyzer-backend"
# })

# traceProvider = TracerProvider(resource=resource)
# processor = BatchSpanProcessor(OTLPSpanExporter(endpoint="<traces-endpoint>/v1/traces"))
# traceProvider.add_span_processor(processor)
# trace.set_tracer_provider(traceProvider)

# reader = PeriodicExportingMetricReader(
#     OTLPMetricExporter(endpoint="<traces-endpoint>/v1/metrics")
# )
# meterProvider = MeterProvider(resource=resource, metric_readers=[reader])
# metrics.set_meter_provider(meterProvider)