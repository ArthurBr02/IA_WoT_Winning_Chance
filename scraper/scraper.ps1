# Script de gestion du scraper avec système de progression
# Usage: .\scraper.ps1 [start|reset|status|clean]

param(
    [Parameter(Position=0)]
    [ValidateSet("start", "reset", "status", "clean")]
    [string]$Action = "start"
)

$ProgressFile = "scraper_progress.json"
$BackupFile = "scraper_progress.backup.json"

function Show-Status {
    Write-Host "=== Status du Scraper ===" -ForegroundColor Cyan

    if (Test-Path $ProgressFile) {
        Write-Host "`nFichier de progression trouvé: $ProgressFile" -ForegroundColor Green

        try {
            $progress = Get-Content $ProgressFile | ConvertFrom-Json

            Write-Host "`nInformations de progression:" -ForegroundColor Yellow
            Write-Host "  - Joueur initial: $($progress.initialPlayerId)"
            Write-Host "  - Démarrage: $($progress.startTime)"
            Write-Host "  - Dernière MAJ: $($progress.lastUpdateTime)"
            Write-Host "  - Batailles récupérées: $($progress.battleDetails.Count)"
            Write-Host "  - Joueurs traités: $($progress.processedPlayerIds.Count)"
            Write-Host "  - Progression: $($progress.currentPlayerIndex)/$($progress.totalPlayersToFetch) joueurs"

            $percentage = [math]::Round(($progress.currentPlayerIndex / $progress.totalPlayersToFetch) * 100, 2)
            Write-Host "  - Pourcentage: $percentage%" -ForegroundColor $(if ($percentage -ge 100) { "Green" } elseif ($percentage -ge 50) { "Yellow" } else { "Red" })

        } catch {
            Write-Host "`nErreur lors de la lecture du fichier de progression" -ForegroundColor Red
            Write-Host $_.Exception.Message -ForegroundColor Red
        }
    } else {
        Write-Host "`nAucune progression trouvée. Le scraper démarrera une nouvelle session." -ForegroundColor Yellow
    }

    if (Test-Path $BackupFile) {
        Write-Host "`nFichier de backup trouvé: $BackupFile" -ForegroundColor Green
    }

    Write-Host ""
}

function Start-Scraper {
    Write-Host "=== Démarrage du Scraper ===" -ForegroundColor Cyan
    Show-Status
    Write-Host "Lancement du scraper..." -ForegroundColor Green
    & .\gradlew run
}

function Reset-Progress {
    Write-Host "=== Réinitialisation de la Progression ===" -ForegroundColor Cyan

    if (Test-Path $ProgressFile) {
        Write-Host "`nSuppression de $ProgressFile..." -ForegroundColor Yellow
        Remove-Item $ProgressFile -Force
        Write-Host "✓ Fichier de progression supprimé" -ForegroundColor Green
    } else {
        Write-Host "`nAucun fichier de progression à supprimer" -ForegroundColor Yellow
    }

    if (Test-Path $BackupFile) {
        Write-Host "Suppression de $BackupFile..." -ForegroundColor Yellow
        Remove-Item $BackupFile -Force
        Write-Host "✓ Fichier de backup supprimé" -ForegroundColor Green
    } else {
        Write-Host "Aucun fichier de backup à supprimer" -ForegroundColor Yellow
    }

    Write-Host "`nLa progression a été réinitialisée. Le prochain démarrage sera une nouvelle session." -ForegroundColor Green
}

function Clean-All {
    Write-Host "=== Nettoyage Complet ===" -ForegroundColor Cyan

    Reset-Progress

    Write-Host "`nNettoyage du build Gradle..." -ForegroundColor Yellow
    & .\gradlew clean

    Write-Host "`n✓ Nettoyage terminé" -ForegroundColor Green
}

# Exécution de l'action demandée
switch ($Action) {
    "start" {
        Start-Scraper
    }
    "status" {
        Show-Status
    }
    "reset" {
        Reset-Progress
    }
    "clean" {
        Clean-All
    }
}

