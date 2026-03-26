"""Command Line Interface for Storage Service"""

import click
import sys
from pathlib import Path
from typing import Optional
from . import StorageService, Config


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """StorageService - Media Backup and Organization Tool"""
    pass


@cli.command()
@click.option(
    "--backup-root",
    "-b",
    required=True,
    help="Root directory for backups",
    type=click.Path(),
)
@click.option(
    "--source",
    "-s",
    required=True,
    help="Source directory to backup",
    type=click.Path(exists=True),
)
@click.option(
    "--skip-duplicates/--no-skip-duplicates",
    default=True,
    help="Skip duplicate files (default: True)",
)
def backup(backup_root: str, source: str, skip_duplicates: bool):
    """Backup media files from source directory"""
    try:
        click.echo(f"📁 Starting backup from: {source}")
        click.echo(f"💾 Backup destination: {backup_root}\n")

        service = StorageService(backup_root)
        stats = service.backup_directory(
            source, skip_duplicates=skip_duplicates, show_progress=True
        )

        click.echo(f"\n✅ Backup Complete!")
        click.echo(f"   Total files processed: {stats.get('total', 0)}")
        click.echo(f"   Successful: {stats.get('successful', 0)}")
        click.echo(f"   Skipped (duplicates): {stats.get('skipped', 0)}")
        click.echo(f"   Failed: {stats.get('failed', 0)}")

    except Exception as e:
        click.echo(f"❌ Error during backup: {str(e)}", err=True)
        sys.exit(1)


@cli.command()
@click.option(
    "--backup-root",
    "-b",
    required=True,
    help="Root directory for backups",
    type=click.Path(),
)
@click.argument("files", nargs=-1, required=True, type=click.Path(exists=True))
def preview(backup_root: str, files):
    """Preview where files would be backed up without actually backing them up"""
    try:
        service = StorageService(backup_root)

        if not files:
            click.echo("❌ Please provide at least one file path", err=True)
            sys.exit(1)

        click.echo("\n📋 Backup Location Preview")
        click.echo("=" * 70)
        click.echo(f"Backup Root: {backup_root}\n")

        all_supported = True
        for file_path in files:
            target_path = service.preview_target_path(file_path)

            if target_path:
                click.echo(f"✅ {file_path}")
                click.echo(f"   → {target_path}\n")
            else:
                click.echo(f"❌ {file_path}")
                click.echo(f"   Media type not supported\n")
                all_supported = False

        if all_supported:
            click.echo("✅ All files can be backed up successfully!")
        else:
            click.echo("⚠️  Some files have unsupported media types")

    except Exception as e:
        click.echo(f"❌ Error during preview: {str(e)}", err=True)
        sys.exit(1)


@cli.command()
@click.option(
    "--backup-root",
    "-b",
    required=True,
    help="Root directory of backups",
    type=click.Path(exists=True),
)
def show_structure(backup_root: str):
    """Display the backup directory structure"""
    try:
        service = StorageService(backup_root)
        service.print_structure()
    except Exception as e:
        click.echo(f"❌ Error: {str(e)}", err=True)
        sys.exit(1)


@cli.command()
@click.option(
    "--backup-root",
    "-b",
    required=True,
    help="Root directory of backups",
    type=click.Path(exists=True),
)
def stats(backup_root: str):
    """Show backup statistics"""
    try:
        service = StorageService(backup_root)
        stats_data = service.get_statistics()

        click.echo("\n📊 Backup Statistics")
        click.echo("=" * 50)
        click.echo(f"Backup Root: {stats_data['backup_root']}")
        click.echo(f"Total Files Backed Up: {stats_data['total_backed_up_files']}")
        click.echo(f"Registry Entries: {stats_data['registry_entries']}")

        dedup = stats_data["deduplication"]
        click.echo(f"\n🔄 Deduplication Stats:")
        click.echo(f"   Total Unique Hashes: {dedup['total_unique_hashes']}")
        click.echo(f"   Total Files Tracked: {dedup['total_files_tracked']}")
        click.echo(f"   Duplicate Groups: {dedup['duplicate_groups']}")
        click.echo(f"   Total Duplicate Files: {dedup['total_duplicate_files']}")

    except Exception as e:
        click.echo(f"❌ Error: {str(e)}", err=True)
        sys.exit(1)


@cli.command()
@click.option(
    "--backup-root",
    "-b",
    required=True,
    help="Root directory of backups",
    type=click.Path(exists=True),
)
def show_config(backup_root: str):
    """Display suggested directory structure"""
    config = Config()
    click.echo(config.get_suggested_structure())


@cli.command()
@click.option(
    "--backup-root",
    "-b",
    required=False,
    help="Root directory of backups",
    type=click.Path(),
)
@click.option(
    "--source",
    "-s",
    required=False,
    help="Source directory to backup",
    type=click.Path(exists=True),
)
def interactive(backup_root: Optional[str], source: Optional[str]):
    """Interactive backup mode"""
    click.echo("\n🎯 StorageService - Interactive Backup Mode")
    click.echo("=" * 50)

    # Get backup root
    if not backup_root:
        backup_root = click.prompt("Enter backup root directory")

    # Show suggested structure
    config = Config()
    click.echo(config.get_suggested_structure())

    # Get source directory
    if not source:
        source = click.prompt("Enter source directory to backup")

    # Confirm
    click.echo(f"\n📋 Backup Details:")
    click.echo(f"   Source: {source}")
    click.echo(f"   Destination: {backup_root}")

    skip_dupes = click.confirm("Skip duplicate files?", default=True)

    if click.confirm("Proceed with backup?"):
        try:
            service = StorageService(backup_root)
            stats = service.backup_directory(
                source, skip_duplicates=skip_dupes, show_progress=True
            )

            click.echo(f"\n✅ Backup Complete!")
            click.echo(f"   Successful: {stats.get('successful', 0)}")
            click.echo(f"   Skipped: {stats.get('skipped', 0)}")
            click.echo(f"   Failed: {stats.get('failed', 0)}")

            service.print_structure()

        except Exception as e:
            click.echo(f"❌ Error: {str(e)}", err=True)
            sys.exit(1)
    else:
        click.echo("❌ Backup cancelled.")


@cli.command()
@click.option(
    "--backup-root",
    "-b",
    required=True,
    help="Root directory of backups",
    type=click.Path(exists=True),
)
def find_duplicates(backup_root: str):
    """Find and display duplicate files"""
    try:
        from .database import Database

        db_path = str(Path(backup_root) / ".storage_service" / "storage.db")
        db = Database(db_path)

        click.echo("\n🔍 Searching for duplicates...\n")

        # Get stats
        stats = db.get_duplicate_stats()
        click.echo(f"📊 Duplicate Statistics:")
        click.echo(f"   Total Unique Hashes: {stats['total_hashes']}")
        click.echo(f"   Duplicate Groups: {stats['duplicate_groups']}")
        click.echo(f"   Total Duplicate Files: {stats['total_duplicate_files']}")

        # Find duplicates
        duplicates = db.find_duplicate_hashes()

        if not duplicates:
            click.echo("\n✅ No duplicates found!")
            return

        click.echo(f"\n🔗 Duplicate Files (Total Groups: {len(duplicates)}):\n")
        for i, (file_hash, file_paths) in enumerate(duplicates.items(), 1):
            click.echo(f"{i}. Hash: {file_hash}")
            
            # Find the FIRST backup path for this hash (since all duplicates map to same content)
            first_backup_path = None
            for path in file_paths:
                backup_entries = db.search_backups(source_path=path)
                if backup_entries:
                    first_backup_path = backup_entries[0].get('target_path', 'N/A')
                    break
            
            # Show all source files and indicate they're duplicates
            for j, path in enumerate(file_paths, 1):
                click.echo(f"   [{j}] Source: {path}")
            
            # Show backup path only once
            if first_backup_path:
                click.echo(f"   └─ Backup (Single Copy): {first_backup_path}")
                click.echo(f"      ⚠️  {len(file_paths)} source files → 1 backup file (duplicates)")
            else:
                click.echo(f"   └─ Backup: Not found in registry")
            click.echo()

    except Exception as e:
        click.echo(f"❌ Error: {str(e)}", err=True)
        sys.exit(1)


@cli.command()
@click.option(
    "--backup-root",
    "-b",
    required=True,
    help="Root directory of backups",
    type=click.Path(exists=True),
)
@click.option(
    "--media-type",
    "-t",
    required=False,
    help="Filter by media type (photos, videos, audio, documents)",
)
@click.option(
    "--path",
    "-p",
    required=False,
    help="Search by file path (partial match)",
)
def search(backup_root: str, media_type: Optional[str], path: Optional[str]):
    """Search backup registry with filters"""
    try:
        from .database import Database

        db_path = str(Path(backup_root) / ".storage_service" / "storage.db")
        db = Database(db_path)

        click.echo("\n🔎 Searching backups...\n")

        # Build search criteria
        search_kwargs = {}
        if media_type:
            search_kwargs["media_type"] = media_type
        if path:
            search_kwargs["source_path"] = path

        results = db.search_backups(**search_kwargs)

        if not results:
            click.echo("❌ No results found!")
            return

        click.echo(f"📁 Found {len(results)} file(s):\n")
        for i, result in enumerate(results, 1):
            click.echo(f"{i}. Source: {result['source_path']}")
            click.echo(f"   Target: {result['target_path']}")
            click.echo(f"   Type: {result['media_type']}")
            click.echo(f"   Status: {result['status']}")
            click.echo(f"   Hash: {result['file_hash']}")
            click.echo(f"   Backed Up: {result['backed_up_at']}")
            click.echo()

    except Exception as e:
        click.echo(f"❌ Error: {str(e)}", err=True)
        sys.exit(1)


@cli.command()
@click.option(
    "--backup-root",
    "-b",
    required=True,
    help="Root directory of backups",
    type=click.Path(exists=True),
)
@click.option(
    "--source",
    "-s",
    required=False,
    default=None,
    help="Delete all backup copies sourced from this original file path",
    type=click.Path(),
)
@click.option(
    "--yes",
    "-y",
    is_flag=True,
    default=False,
    help="Skip confirmation prompt",
)
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="Show what would be deleted without actually deleting anything",
)
@click.argument("files", nargs=-1, type=click.Path())
def delete(backup_root: str, source: Optional[str], yes: bool, dry_run: bool, files):
    """Delete backed-up files from the backup storage.

    Accepts one or more backup TARGET paths as arguments, or use --source to
    delete by the original source file path.

    Examples:

    \b
      # Delete specific backup files by their backup path
      storage-service delete -b /backup /backup/Photos/2023/01/ab/photo.jpg

    \b
      # Delete all backups that were sourced from a given file
      storage-service delete -b /backup --source /original/photo.jpg
    """
    try:
        if not source and not files:
            click.echo("❌ Provide at least one file path or use --source.", err=True)
            sys.exit(1)

        service = StorageService(backup_root)

        # Collect what will be deleted so we can confirm
        if source:
            from .database import Database
            from pathlib import Path as _Path
            db_path = str(_Path(backup_root) / ".storage_service" / "storage.db")
            db = Database(db_path)
            entries = db.search_backups(source_path=source)
            entries = [e for e in entries if e["source_path"] == source]

            if not entries:
                click.echo(f"⚠️  No backups found for source: {source}")
                return

            click.echo(f"\n🗑️  Backups to delete for source: {source}")
            for e in entries:
                marker = "[DRY RUN] " if dry_run else ""
                click.echo(f"   {marker}{e['target_path']}")
        else:
            click.echo(f"\n🗑️  Files to delete:")
            for f in files:
                marker = "[DRY RUN] " if dry_run else ""
                click.echo(f"   {marker}{f}")

        if dry_run:
            click.echo("\n✅ Dry run complete. No files were deleted.")
            return

        if not yes:
            if not click.confirm("\nProceed with deletion?"):
                click.echo("❌ Deletion cancelled.")
                return

        click.echo()

        if source:
            stats = service.delete_by_source(source)
            click.echo(f"✅ Deleted: {stats['deleted']}")
            if stats["not_found"]:
                click.echo(f"⚠️  Not found (stale records cleaned): {stats['not_found']}")
            if stats["failed"]:
                click.echo(f"❌ Failed: {stats['failed']}", err=True)
        else:
            deleted = not_found = failed = 0
            for f in files:
                status = service.delete_file(f)
                if status == "success":
                    click.echo(f"✅ Deleted: {f}")
                    deleted += 1
                elif status == "not_found":
                    click.echo(f"⚠️  Not found: {f}")
                    not_found += 1
                else:
                    click.echo(f"❌ Failed: {f}", err=True)
                    failed += 1

            click.echo(f"\nSummary — Deleted: {deleted}  Not found: {not_found}  Failed: {failed}")

    except Exception as e:
        click.echo(f"❌ Error: {str(e)}", err=True)
        sys.exit(1)


def main():
    """Main entry point"""
    cli()


if __name__ == "__main__":
    main()
