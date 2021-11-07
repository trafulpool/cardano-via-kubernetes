# Cardano via Kubernetes

This repo consists of a growing set of tools for running Cardano nodes via Kuberentes. It starts as an unsorted bag of scripts, yamls and docs. Time permiting, it will become a K8s operator with CRDs reprenting Cardano building blocks (relays, block-producers, explorer, db-sync, etc).

## Unboxing

### Topology Updater CronJob

This is a Cardano topology updater implemented as a k8s CronJob which persists the output directly into a k8s ConfigMap. It's meant to be used SPO running their relay nodes within a k8s cluster. The update logic is inspired on the one provided by Guild Opeators.

### Tip Notifier

This is a worker written in python just for notifying a relay node tip. It's meant to be ran as a secondary container in the same pod as the relay node (so that they share the same outbound IP address and for localhost access to the EKG endpoint)