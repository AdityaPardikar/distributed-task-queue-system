"""Basic OpenTelemetry setup and FastAPI instrumentation."""

from typing import Optional

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

TRACER: Optional[trace.Tracer] = None


def configure_tracing(service_name: str = "taskflow-api", endpoint: Optional[str] = None) -> trace.Tracer:
    """Configure a basic tracer provider with optional OTLP HTTP exporter."""
    global TRACER
    resource = Resource.create({"service.name": service_name})
    provider = TracerProvider(resource=resource)

    if endpoint:
        exporter = OTLPSpanExporter(endpoint=endpoint)
        processor = BatchSpanProcessor(exporter)
        provider.add_span_processor(processor)

    trace.set_tracer_provider(provider)
    TRACER = trace.get_tracer(service_name)
    return TRACER


def get_tracer() -> trace.Tracer:
    """Return configured tracer."""
    return TRACER or trace.get_tracer("taskflow-api")
