#!/usr/bin/env python3
"""TaskFlow CLI Management Tool.

Provides command-line utilities for managing the TaskFlow distributed
task queue system: worker management, task inspection, backup/restore,
maintenance, and configuration validation.

Usage:
    python scripts/taskctl.py status
    python scripts/taskctl.py config validate
    python scripts/taskctl.py backup create [--name NAME]
    python scripts/taskctl.py backup list
    python scripts/taskctl.py maintenance run
    python scripts/taskctl.py tasks stats
    python scripts/taskctl.py health
"""

import argparse
import json
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def cmd_status(args):
    """Show overall system status."""
    from src.config import get_settings

    settings = get_settings()
    print(f"TaskFlow {settings.VERSION}")
    print(f"  Environment: {settings.APP_ENV}")
    print(f"  Database:    {settings.DATABASE_URL.split('@')[-1] if '@' in settings.DATABASE_URL else settings.DATABASE_URL}")
    print(f"  Debug:       {settings.DEBUG}")

    # Test database connectivity
    try:
        from sqlalchemy import create_engine, text
        engine = create_engine(settings.DATABASE_URL)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print(f"  DB Status:   Connected")
    except Exception as e:
        print(f"  DB Status:   ERROR - {e}")


def cmd_config_validate(args):
    """Validate configuration."""
    from src.operations.config_validator import ConfigValidator

    validator = ConfigValidator(env_file=".env")
    report = validator.validate_all()

    print(f"\nConfiguration Validation Report")
    print(f"{'=' * 50}")
    print(f"Valid: {'YES' if report.valid else 'NO'}")
    print(f"Errors: {report.errors}")
    print(f"Warnings: {report.warnings}")
    print()

    for result in report.results:
        icon = "✓" if result.passed else ("✗" if result.severity == "error" else "⚠")
        print(f"  {icon} [{result.severity.upper():7s}] {result.check_name}: {result.message}")

    sys.exit(0 if report.valid else 1)


def cmd_config_show(args):
    """Show current configuration (masked)."""
    from src.operations.config_validator import ConfigValidator

    validator = ConfigValidator(env_file=".env")
    config = validator.get_current_config()

    print("\nCurrent Configuration:")
    print(f"{'=' * 50}")
    for key, value in config.items():
        status = value if value else "(not set)"
        print(f"  {key}: {status}")


def cmd_backup_create(args):
    """Create a database backup."""
    from src.config import get_settings
    from src.operations.backup import BackupManager

    settings = get_settings()
    manager = BackupManager(settings.DATABASE_URL)

    print("Creating backup...")
    try:
        backup = manager.create_backup(backup_name=args.name)
        print(f"  File:     {backup.filename}")
        print(f"  Path:     {backup.filepath}")
        print(f"  Size:     {backup.size_bytes:,} bytes")
        print(f"  Checksum: {backup.checksum[:16]}...")
        print(f"  Created:  {backup.created_at}")
        print("Backup created successfully!")
    except Exception as e:
        print(f"ERROR: Backup failed - {e}")
        sys.exit(1)


def cmd_backup_list(args):
    """List available backups."""
    from src.config import get_settings
    from src.operations.backup import BackupManager

    settings = get_settings()
    manager = BackupManager(settings.DATABASE_URL)
    backups = manager.list_backups()

    if not backups:
        print("No backups found.")
        return

    print(f"\nAvailable Backups ({len(backups)} total):")
    print(f"{'=' * 70}")
    for b in backups:
        print(f"  {b.filename:40s}  {b.size_bytes:>10,} bytes  {b.created_at[:19]}")


def cmd_backup_restore(args):
    """Restore from a backup."""
    from src.config import get_settings
    from src.operations.backup import BackupManager

    settings = get_settings()
    manager = BackupManager(settings.DATABASE_URL)

    if not args.yes:
        response = input(f"Restore from {args.path}? This will overwrite current data. [y/N] ")
        if response.lower() != "y":
            print("Aborted.")
            return

    print(f"Restoring from {args.path}...")
    try:
        success = manager.restore_backup(args.path)
        if success:
            print("Restore completed successfully!")
        else:
            print("ERROR: Restore failed")
            sys.exit(1)
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)


def cmd_maintenance_run(args):
    """Run database maintenance."""
    from src.db.session import SessionLocal
    from src.operations.maintenance import MaintenanceManager

    manager = MaintenanceManager(SessionLocal)
    print("Running maintenance operations...")

    results = manager.run_full_maintenance()
    for r in results:
        icon = "✓" if r.success else "✗"
        print(f"  {icon} {r.operation}: {r.message} ({r.duration_ms:.1f}ms)")

    if all(r.success for r in results):
        print("\nAll maintenance operations completed successfully!")
    else:
        print("\nSome operations failed. Check logs for details.")
        sys.exit(1)


def cmd_tasks_stats(args):
    """Show task statistics."""
    from sqlalchemy import text
    from src.db.session import SessionLocal

    session = SessionLocal()
    try:
        result = session.execute(text(
            "SELECT status, count(*) FROM tasks GROUP BY status ORDER BY count(*) DESC"
        ))
        rows = result.fetchall()

        print("\nTask Statistics:")
        print(f"{'=' * 40}")
        total = 0
        for status, count in rows:
            print(f"  {status:20s}: {count:>8,}")
            total += count
        print(f"  {'TOTAL':20s}: {total:>8,}")
    except Exception as e:
        print(f"ERROR: {e}")
    finally:
        session.close()


def cmd_tasks_cleanup(args):
    """Clean up old tasks."""
    from src.db.session import SessionLocal
    from src.operations.maintenance import MaintenanceManager

    manager = MaintenanceManager(SessionLocal)
    result = manager.cleanup_old_tasks(days=args.days)

    if result.success:
        print(f"Cleaned up: {result.details.get('cleaned_count', 0)} tasks")
    else:
        print(f"ERROR: {result.message}")
        sys.exit(1)


def cmd_health(args):
    """Show system health."""
    from src.db.session import SessionLocal
    from src.operations.maintenance import MaintenanceManager

    manager = MaintenanceManager(SessionLocal)
    health = manager.get_system_health()

    print(f"\nSystem Health: {health['status'].upper()}")
    print(f"Timestamp: {health['timestamp']}")
    print(f"{'=' * 50}")

    for check_name, check_data in health.get("checks", {}).items():
        status = check_data.get("status", "unknown")
        icon = "✓" if status == "healthy" else ("⚠" if status == "warning" else "✗")
        extra = ""
        if "size" in check_data:
            extra = f" ({check_data['size']})"
        elif "active_connections" in check_data:
            extra = f" ({check_data['active_connections']} connections)"
        elif "table_count" in check_data:
            extra = f" ({check_data['table_count']} tables)"
        print(f"  {icon} {check_name}: {status}{extra}")


def main():
    parser = argparse.ArgumentParser(
        prog="taskctl",
        description="TaskFlow Management CLI",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # status
    subparsers.add_parser("status", help="Show system status")

    # config
    config_parser = subparsers.add_parser("config", help="Configuration management")
    config_sub = config_parser.add_subparsers(dest="config_action")
    config_sub.add_parser("validate", help="Validate configuration")
    config_sub.add_parser("show", help="Show current configuration")

    # backup
    backup_parser = subparsers.add_parser("backup", help="Backup management")
    backup_sub = backup_parser.add_subparsers(dest="backup_action")
    create_parser = backup_sub.add_parser("create", help="Create backup")
    create_parser.add_argument("--name", help="Backup name")
    backup_sub.add_parser("list", help="List backups")
    restore_parser = backup_sub.add_parser("restore", help="Restore from backup")
    restore_parser.add_argument("path", help="Backup file path")
    restore_parser.add_argument("--yes", "-y", action="store_true", help="Skip confirmation")

    # maintenance
    maint_parser = subparsers.add_parser("maintenance", help="Database maintenance")
    maint_sub = maint_parser.add_subparsers(dest="maint_action")
    maint_sub.add_parser("run", help="Run maintenance")

    # tasks
    tasks_parser = subparsers.add_parser("tasks", help="Task management")
    tasks_sub = tasks_parser.add_subparsers(dest="tasks_action")
    tasks_sub.add_parser("stats", help="Show task statistics")
    cleanup_parser = tasks_sub.add_parser("cleanup", help="Clean up old tasks")
    cleanup_parser.add_argument("--days", type=int, default=90, help="Age threshold in days")

    # health
    subparsers.add_parser("health", help="System health check")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    commands = {
        "status": cmd_status,
        "health": cmd_health,
    }

    if args.command in commands:
        commands[args.command](args)
    elif args.command == "config":
        if args.config_action == "validate":
            cmd_config_validate(args)
        elif args.config_action == "show":
            cmd_config_show(args)
        else:
            config_parser.print_help()
    elif args.command == "backup":
        if args.backup_action == "create":
            cmd_backup_create(args)
        elif args.backup_action == "list":
            cmd_backup_list(args)
        elif args.backup_action == "restore":
            cmd_backup_restore(args)
        else:
            backup_parser.print_help()
    elif args.command == "maintenance":
        if args.maint_action == "run":
            cmd_maintenance_run(args)
        else:
            maint_parser.print_help()
    elif args.command == "tasks":
        if args.tasks_action == "stats":
            cmd_tasks_stats(args)
        elif args.tasks_action == "cleanup":
            cmd_tasks_cleanup(args)
        else:
            tasks_parser.print_help()


if __name__ == "__main__":
    main()
