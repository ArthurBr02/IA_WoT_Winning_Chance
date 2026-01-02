Je veux une application mobile Android faite avec Java. Cette application servira à faire tourner en tâche de fond un programme de scraping web.

Le développement de cette application devra se baser sur le code existant d'un programme de scraping web écrit en Java, qui se trouve dans le répertoire `./scraper/`. Le but est d'intégrer ce programme dans une application Android afin qu'il puisse fonctionner en arrière-plan tout en offrant une interface utilisateur pour contrôler et surveiller le processus de scraping.

Le projet se situera dans le répertoire `./mobile/` et devra être structuré de manière à séparer clairement la logique de l'application Android de celle du programme de scraping web.

Cette application devra mettre en œuvre les fonctionnalités suivantes :
- Démarrer et arrêter le programme de scraping web via une interface utilisateur simple.
- Afficher les journaux d'activité du programme de scraping en temps réel.
- Gérer les permissions nécessaires pour accéder à Internet et au stockage si besoin.
- Envoyer des notifications lorsque certaines actions sont effectuées par le programme de scraping (par exemple, lorsqu'une tâche est terminée).
- Permettre la configuration des paramètres du programme de scraping (par exemple, l'intervalle de temps entre les scrapes, les URL cibles, etc.) via l'interface utilisateur.
- Assurer que le programme de scraping continue de fonctionner même lorsque l'application est en arrière-plan ou lorsque l'appareil est en veille. (très important)
- Gérer les erreurs et les exceptions de manière appropriée, en informant l'utilisateur si nécessaire.
- Fournir une option pour exporter les données collectées par le programme de scraping vers un fichier local en json.
- Il faut que l'application enregistre la progression du scraping pour pouvoir la reprendre en cas d'arrêt inattendu (par exemple, en cas de fermeture forcée de l'application, de perte de connexion internet ou de redémarrage de l'appareil). Je veux qu'elle reprenne automatiquement le scraping à partir du dernier point sauvegardé (peu importe la progression, il faut reprndre exactement là où ça s'est arrêté sans perdre les données déjà récupérées, donc faire un export régulier des données pour ne rien perdre, extrêmement important).
- Le scraping est divisé en trois étapes: récupération des CombinedBattles, récupération des BattleDetails, et récupération des Players. Chaque étape doit être clairement indiquée dans l'interface utilisateur avec une barre de progression.

Le fichier d'export sera au format suivant:
```json
{
  "combinedBattles": [ ... ],
  "battleDetails": [ ... ],
  "players": [ ... ]
}
```

L'application doit être conçue en respectant les bonnes pratiques de développement Android, en utilisant des composants tels que les Services pour le scraping en arrière-plan, les Broadcast Receivers pour les notifications, et les SharedPreferences pour la gestion des paramètres utilisateur.