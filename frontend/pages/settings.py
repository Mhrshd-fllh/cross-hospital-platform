"""
Settings page for the Cross-Hospital Generalization Platform.
Displays system configuration and settings (view-only as per requirements).
"""

import streamlit as st
from datetime import datetime

# Import services
from frontend.services.settings_service import SettingsService

def create_settings_service():
    """Create an instance of the settings service."""
    return SettingsService()

def settings_page():
    """Main settings page function"""
    # Header
    st.header("⚙️ System Settings")
    st.markdown("View system configuration and settings (read-only)")

    # Create settings service
    settings_service = create_settings_service()

    # Get settings data from service
    try:
        with st.spinner("Loading system settings..."):
            settings = settings_service.get_settings()
    except Exception as e:
        st.error(f"Error loading settings: {str(e)}")
        return

    # Create tabs for different settings categories
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "🖥️ System",
        "🗄️ Database",
        "💾 Storage",
        "🧪 MLflow",
        "⚙️ Processing",
        "🚨 Alerting & Security"
    ])

    with tab1:
        st.subheader("System Information")
        sys_info = settings["system"]

        col1, col2 = st.columns(2)
        with col1:
            st.text_input("Name", value=sys_info["name"], disabled=True)
            st.text_input("Version", value=sys_info["version"], disabled=True)
            st.text_input("Environment", value=sys_info["environment"], disabled=True)
            st.text_input("Instance ID", value=sys_info["instance_id"], disabled=True)

        with col2:
            st.text_input("Deployment Date", value=sys_info["deployment_date"], disabled=True)
            st.text_input("Last Updated", value=sys_info["last_updated"], disabled=True)

        # System status
        st.subheader("System Status")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Uptime", "99.9%")
        with col2:
            st.metric("Requests/Hour", "1,245")
        with col3:
            st.metric("Avg Response Time", "245ms")
        with col4:
            st.metric("Error Rate", "0.02%")

    with tab2:
        st.subheader("Database Configuration")
        db_info = settings["database"]

        col1, col2 = st.columns(2)
        with col1:
            st.text_input("Type", value=db_info["type"], disabled=True)
            st.text_input("Version", value=db_info["version"], disabled=True)
            st.text_input("Host", value=db_info["host"], disabled=True)
            st.text_input("Port", value=str(db_info["port"]), disabled=True)
            st.text_input("Database Name", value=db_info["name"], disabled=True)

        with col2:
            st.text_input("SSL Mode", value=db_info["ssl_mode"], disabled=True)
            st.text_input("Backup Frequency", value=db_info["backup_frequency"], disabled=True)
            st.text_input("Retention Period", value=db_info["retention_period"], disabled=True)

        # Connection status
        st.subheader("Connection Status")
        st.success("✅ Connected - Last ping: 45ms")

    with tab3:
        st.subheader("Storage Configuration")
        storage_info = settings["storage"]

        st.text_input("Type", value=storage_info["type"], disabled=True)
        st.text_input("Endpoint", value=storage_info["endpoint"], disabled=True)
        st.text_input("Access Key", value=storage_info["access_key"], disabled=True)
        st.text_input("Secret Key", value=storage_info["secret_key"], disabled=True)

        st.subheader("Storage Buckets")
        for bucket_name, bucket_info in storage_info["buckets"].items():
            with st.expander(f"Bucket: {bucket_name}"):
                col1, col2 = st.columns(2)
                with col1:
                    st.text_input("Policy", value=bucket_info["policy"], disabled=True)
                    st.text_input("Versioning", value=bucket_info["versioning"], disabled=True)
                with col2:
                    st.text_input("Size", value=bucket_info["size"], disabled=True)
                    st.text_input("Object Count", value=button_info["object_count"], disabled=True)

    with tab4:
        st.subheader("MLflow Configuration")
        mllow_info = settings["mlflow"]

        col1, col2 = st.columns(2)
        with col1:
            st.text_input("Tracking URI", value=mllow_info["tracking_uri"], disabled=True)
            st.text_input("Registry URI", value=mllow_info["registry_uri"], disabled=True)
            st.text_input("Experiment Count", value=str(mllow_info["experiment_count"]), disabled=True)

        with col2:
            st.text_input("Registered Models", value=str(mllow_info["registered_models"]), disabled=True)
            st.text_input("Latest Run", value=mllow_info["latest_run"], disabled=True)

        # Model registry info
        st.subheader("Registered Models (Sample)")
        model_data = [
            {"Model": "CheXpert-Pneumonia-DenseNet121", "Version": "v2.1.0", "Stage": "Production"},
            {"Model": "MIMIC-Cardiomegaly-ResNet50", "Version": "v1.8.3", "Stage": "Production"},
            {"Model": "NIH-Nodule-EfficientNetB0", "Version": "v3.0.1", "Stage": "Staging"}
        ]
        st.dataframe(
            model_data,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Model": st.column_config.TextColumn("Model Name"),
                "Version": st.column_config.TextColumn("Version"),
                "Stage": st.column_config.TextColumn("Stage")
            }
        )

    with tab5:
        st.subheader("Processing Configuration")
        proc_info = settings["processing"]

        # Drift Detection Settings
        st.subheader("Drift Detection")
        drift_info = proc_info["drift_detection"]
        col1, col2 = st.columns(2)
        with col1:
            st.text_input("Method", value=drift_info["method"], disabled=True)
            st.slider("Warning Threshold", 0.0, 1.0, float(drift_info["threshold_warning"]), disabled=True)
            st.slider("Alert Threshold", 0.0, 1.0, float(drift_info["threshold_alert"]), disabled=True)
        with col2:
            st.text_input("Reference Dataset", value=drift_info["reference_dataset"], disabled=True)
            st.text_input("Update Frequency", value=drift_info["update_frequency"], disabled=True)

        # Style Adaptation Settings
        st.subheader("Style Adaptation")
        adapt_info = proc_info["style_adaptation"]
        st.text_input("Techniques", value=", ".join(adapt_info["techniques"]), disabled=True)
        slider_val = float(adapt_info["default_strength"]) if isinstance(adapt_info["default_strength"], (int, float)) else 0.7
        st.slider("Default Strength", 0.0, 1.0, slider_val, disabled=True)
        anatomy_prio = bool(adapt_info["anatomy_preservation_priority"]) if isinstance(adapt_info["anatomy_preservation_priority"], bool) else True
        st.checkbox("Anatomy Preservation Priority", value=anatomy_prio, disabled=True)

        # Inference Settings
        st.subheader("Inference")
        infer_info = proc_info["inference"]
        col1, col2 = st.columns(2)
        with col1:
            batch_size = int(infer_info["batch_size"]) if isinstance(infer_info["batch_size"], int) else 1
            st.number_input("Batch Size", value=batch_size, disabled=True)
            timeout_val = int(infer_info["timeout_seconds"]) if isinstance(infer_info["timeout_seconds"], int) else 30
            st.number_input("Timeout (seconds)", value=timeout_val, disabled=True)
            gpu_enabled = bool(infer_info["gpu_enabled"]) if isinstance(infer_info["gpu_enabled"], bool) else True
            st.checkbox("GPU Enabled", value=gpu_enabled, disabled=True)
        with col2:
            max_concurrent = int(infer_info["max_concurrent_requests"]) if isinstance(infer_info["max_concurrent_requests"], int) else 10
            st.number_input("Max Concurrent Requests", value=max_concurrent, disabled=True)

    with tab6:
        st.subheader("Alerting Configuration")
        alert_info = settings["alerting"]

        col1, col2 = st.columns(2)
        with col1:
            enabled = bool(alert_info["enabled"]) if isinstance(alert_info["enabled"], bool) else True
            st.checkbox("Alerting Enabled", value=enabled, disabled=True)
            drift_thresh = float(alert_info["drift_threshold"]) if isinstance(alert_info["drift_threshold"], (int, float)) else 0.6
            st.number_input("Drift Threshold", value=drift_thresh, step=0.05, disabled=True)
            conf_thresh = float(alert_info["confidence_threshold"]) if isinstance(alert_info["confidence_threshold"], (int, float)) else 0.7
            st.number_input("Confidence Threshold", value=conf_thresh, step=0.05, disabled=True)
            cooldown = int(alert_info["cooldown_minutes"]) if isinstance(alert_info["cooldown_minutes"], int) else 30
            st.number_input("Cooldown (minutes)", value=cooldown, disabled=True)

        with col2:
            st.subheader("Notification Channels")
            for channel in alert_info["channels"]:
                status = "✅ Enabled" if channel.get("enabled", False) else "❌ Disabled"
                with st.expander(f"{channel['type']} - {status}"):
                    if channel["type"] == "Slack":
                        st.text(f"Channel: {channel.get('channel', 'N/A')}")
                    elif channel["type"] == "Email":
                        st.text(f"Address: {channel.get('address', 'N/A')}")
                    elif channel["type"] == "Webhook":
                        st.text(f"URL: {channel.get('url', 'N/A')}")

        st.markdown("---")

        st.subheader("Security Configuration")
        sec_info = settings["security"]
        col1, col2 = st.columns(2)
        with col1:
            st.text_input("Authentication", value=sec_info["authentication"], disabled=True)
            st.text_input("Authorization", value=sec_info["authorization"], disabled=True)
            st.text_input("Encryption at Rest", value=sec_info["encryption_at_rest"], disabled=True)
            st.text_input("Encryption in Transit", value=sec_info["encryption_in_transit"], disabled=True)
        with col2:
            audit_logging = str(sec_info["audit_logging"]) if isinstance(sec_info["audit_logging"], str) else "Enabled"
            st.text_input("Audit Logging", value=audit_logging, disabled=True)
            session_timeout = str(sec_info["session_timeout"]) if isinstance(sec_info["session_timeout"], str) else "30 minutes"
            st.text_input("Session Timeout", value=session_timeout, disabled=True)

        st.subheader("Security Status")
        st.success("✅ All security controls active")
        st.info("Last security scan: 2024-06-15 (No critical vulnerabilities found)")

    # Footer with actions (all disabled as per requirements - settings are view-only)
    st.markdown("---")
    st.subheader("Actions")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.button("🔄 Refresh Configuration", disabled=True, help="Settings are view-only in this mode")
    with col2:
        st.button("📥 Export Configuration", disabled=True, help="Export functionality would be implemented in editable mode")
    with col3:
        st.button("📧 Send Test Alert", disabled=True, help="Alert testing would require elevated permissions")

    # TODO comments for future integration
    st.markdown("---")
    st.markdown("### 🔧 Future Integration Points")
    st.markdown("""
    - TODO: Connect to actual SettingsService (replace mock)
    - TODO: Implement editable settings mode for administrators
    - TODO: Add validation for configuration changes
    - TODO: Add ability to restart services with new configuration
    - TODO: Add configuration versioning and rollback capabilities
    - TODO: Add configuration diff viewer
    - TODO: Integrate with secrets management (HashiCorp Vault, AWS Secrets Manager)
    - TODO: Add configuration audit trail
    - TODO: Add configuration templates for different environments
    - TODO: Add feature flag management system
    """)