# Retrieval Report

Mean Recall@10: 1.0000
Precision@1: 0.8750
Precision@3: 0.5833
Precision@5: 0.4500
Average Retrieval Latency: 26.98 ms

## Per-Query Recall@10

| Case | Category | Route | Recall@10 | Retrieved | Failures |
|------|----------|-------|-----------|-----------|----------|
| rec_001 | recommendation | RECOMMEND | 1.0000 | Python (New), Mining Engineering (New), Mineral Engineering (New), .NET Framework 4.5, Geoinformatics Engineering (New), .NET MVC (New), Mechanical Engineering (New), .NET MVVM (New), .NET WCF (New), Instrumentation Engineering (New) |  |
| rec_002 | recommendation | RECOMMEND | 1.0000 | Data Science (New), Automata Data Science (New), Automata Data Science Pro (New), Computer Science (New), Data Warehousing Concepts, Programming Concepts, Pharmaceutical Science (New), Econometrics (New), Food Science (New), Geoinformatics Engineering (New) |  |
| rec_003 | recommendation | RECOMMEND | 1.0000 | Java Platform Enterprise Edition 7 (Java EE 7), Java Design Patterns (New), Java 8 (New), Java Web Services (New), Java Frameworks (New), Java 2 Platform Enterprise Edition 1.4 Fundamental, Core Java (Advanced Level) (New), Core Java (Entry Level) (New), Enterprise Java Beans (New), Automata - Fix (New) |  |
| rec_004 | recommendation | RECOMMEND | 1.0000 | SQL (New), SQL Server (New), SQL Server Analysis Services (SSAS) (New), SQL Server Integration Services (SSIS) (New), SQL Server Reporting Services (SSRS) (New), Oracle PL/SQL (New), Microsoft SQL Server 2014 Programming, Automata - SQL (New), Teradata Development (New), Oracle DBA (Entry Level) (New) |  |
| refine_001 | refinement | REFINE | 1.0000 | Python (New), Informatica (Developer) (New), Agile Software Development, Drupal (New), .NET Framework 4.5, .NET MVC (New), .NET MVVM (New), .NET WCF (New), .NET WPF (New), iOS Development (New) |  |
| refine_002 | refinement | REFINE | 1.0000 | Python (New), Written English v1, English Comprehension (New), Spelling (U.S.) (New), Count Out The Money, Smart Interview Live Coding, SVAR - Spoken English (U.K.), Typing (New), SHL Verify Interactive - Inductive Reasoning, SVAR - Spoken English (AUS) |  |
| mt_001 | multi_turn | RECOMMEND | 1.0000 | Instrumentation Engineering (New), .NET Framework 4.5, Mechanical Engineering (New), .NET MVC (New), Civil Engineering (New), .NET MVVM (New), Electronics & Telecommunications Engineering (New), .NET WCF (New), Industrial Engineering (New), .NET WPF (New) |  |
| mt_002 | multi_turn | RECOMMEND | 1.0000 | Python (New), .NET Framework 4.5, .NET MVC (New), .NET MVVM (New), .NET WCF (New), Computer Science (New), .NET WPF (New), .NET XAML (New), C Programming (New), Data Science (New) |  |

## Root-Cause Analysis

Failures indicate cases where routing, catalog grounding, or ranking should be inspected before submission.

## Ranking Improvement Suggestions

Prioritize exact catalog skill names, explicit exclusions, duration constraints, and role/seniority metadata when Recall@10 drops below 1.0.
