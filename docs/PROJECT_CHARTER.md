
Project Charter
Objective

Determine whether a lightweight, reproducible longitudinal observability layer
for GTFS Schedule feeds provides useful information not already adequately
served by point-in-time validators and ordinary file diffs.

Core distinction

This project separates:

validation — whether one feed conforms to rules;
diffing — what changed between two files;
observability — preserving comparable evidence across successive feed
versions so operational changes can be detected and interpreted.
Candidate observability dimensions

Candidate dimensions are hypotheses, not committed features:

provenance and feed identity;
publication/version churn;
entity-count change;
service-horizon change;
route/trip/service disappearance;
structural churn;
repeated identical publication;
validator-result change;
temporal coverage stability.
Non-goals

At this stage:

no web dashboard;
no hosted service;
no alerting;
no arbitrary feed-quality score;
no new GTFS validation rules;
no database;
no dependency on proprietary APIs;
no claim that change equals error.
First feasibility gate

V0 succeeds if the same GTFS ZIP produces the same semantic manifest on
repeated runs and the manifest captures enough provenance to support later
comparison.

Only after this is established should pairwise comparison be implemented.
