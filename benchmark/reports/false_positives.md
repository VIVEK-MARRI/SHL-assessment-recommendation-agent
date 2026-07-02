# False Positive Pattern Analysis (Stress Benchmark)

## Top-20 Over-Retrieved Assessments (Irrelevant Retrievals)

| Rank | ID | Name | False Positive Count | Total Retrievals | FP Rate | Keys | Categories Appearing |
|------|----|------|---------------------|-----------------|---------|------|---------------------|
| 1 | 3976 | Verify Interactive G+ Candidate Report | 290 | 290 | 100.0% | Ability & Aptitude | ability_aptitude, assessment_exercises, backend, b |
| 2 | 4130 | Salesforce Development (New) | 268 | 281 | 95.4% | Knowledge & Skills | ability_aptitude, assessment_exercises, backend, b |
| 3 | 4019 | Adobe Experience Manager (New) | 250 | 274 | 91.2% | Knowledge & Skills | ability_aptitude, backend, biodata_situational_jud |
| 4 | 382 | Following Instructions v1 - UK (R1) | 203 | 225 | 90.2% | Knowledge & Skills | ability_aptitude, assessment_exercises, backend, b |
| 5 | 4062 | Drupal (New) | 202 | 213 | 94.8% | Knowledge & Skills | ability_aptitude, backend, biodata_situational_jud |
| 6 | 4080 | HTML/CSS (New) | 187 | 188 | 99.5% | Knowledge & Skills | ability_aptitude, backend, cloud, cognitive, custo |
| 7 | 4040 | ITIL (IT Infrastructure Library) (New) | 184 | 193 | 95.3% | Knowledge & Skills | ability_aptitude, assessment_exercises, backend, b |
| 8 | 4171 | Search Engine Optimization (New) | 180 | 182 | 98.9% | Knowledge & Skills | ability_aptitude, assessment_exercises, backend, b |
| 9 | 4116 | Operations Management (New) | 176 | 223 | 78.9% | Knowledge & Skills | ability_aptitude, assessment_exercises, backend, b |
| 10 | 3941 | Verify - Following Instructions | 174 | 174 | 100.0% | Ability & Aptitude | ability_aptitude, assessment_exercises, backend, b |
| 11 | 383 | Following Instructions v1 - US (R2) | 169 | 188 | 89.9% | Knowledge & Skills | ability_aptitude, backend, biodata_situational_jud |
| 12 | 3827 | .NET Framework 4.5 | 166 | 179 | 92.7% | Knowledge & Skills | backend, cloud, customer_service, data_science, de |
| 13 | 4072 | Front Office Management (New) | 162 | 162 | 100.0% | Knowledge & Skills | ability_aptitude, assessment_exercises, backend, b |
| 14 | 4101 | Desktop Support (New) | 156 | 179 | 87.2% | Knowledge & Skills | ability_aptitude, assessment_exercises, backend, b |
| 15 | 4094 | .NET MVC (New) | 155 | 169 | 91.7% | Knowledge & Skills | backend, cloud, cybersecurity, data_science, devel |
| 16 | 333 | Interviewing and Hiring Concepts (U.S.) | 154 | 162 | 95.1% | Knowledge & Skills | ability_aptitude, assessment_exercises, backend, b |
| 17 | 116 | Software Business Analysis | 154 | 218 | 70.6% | Knowledge & Skills | ability_aptitude, assessment_exercises, backend, b |
| 18 | 4092 | Microsoft Dynamics Development (New) | 154 | 165 | 93.3% | Knowledge & Skills | ability_aptitude, backend, biodata_situational_jud |
| 19 | 3974 | Verify Interactive G+ Report | 148 | 148 | 100.0% | Ability & Aptitude | ability_aptitude, backend, biodata_situational_jud |
| 20 | 4099 | .NET MVVM (New) | 145 | 151 | 96.0% | Knowledge & Skills | backend, cloud, data_science, development_360, dev |

## Cross-Category FP Analysis


- **[3976] Verify Interactive G+ Candidate Report**: FP across categories: {'personality_behavior': 16, 'testing': 8, 'data_science': 11, 'ability_aptitude': 3, 'devops': 30, 'finance': 1, 'biodata_situational_judgment': 7, 'management': 5, 'hr': 2, 'cybersecurity': 28, 'general': 6, 'frontend': 26, 'backend': 27, 'entry_level': 1, 'cloud': 14, 'sql': 4, 'java': 4, 'development_360': 26, 'python': 11, 'knowledge_skills': 48, 'simulations': 4, 'mobile': 6, 'assessment_exercises': 2}

- **[4130] Salesforce Development (New)**: FP across categories: {'personality_behavior': 13, 'testing': 6, 'data_science': 15, 'ability_aptitude': 9, 'devops': 41, 'finance': 1, 'biodata_situational_judgment': 5, 'management': 13, 'hr': 1, 'cybersecurity': 4, 'general': 4, 'frontend': 26, 'backend': 24, 'cloud': 16, 'cognitive': 1, 'java': 3, 'development_360': 16, 'python': 7, 'knowledge_skills': 38, 'simulations': 1, 'mobile': 8, 'sales': 14, 'assessment_exercises': 1, 'marketing': 1}

- **[4019] Adobe Experience Manager (New)**: FP across categories: {'personality_behavior': 12, 'testing': 18, 'data_science': 12, 'ability_aptitude': 2, 'devops': 12, 'finance': 1, 'biodata_situational_judgment': 1, 'management': 51, 'hr': 6, 'cybersecurity': 6, 'general': 12, 'frontend': 8, 'backend': 5, 'cloud': 28, 'cognitive': 7, 'sql': 2, 'java': 6, 'development_360': 11, 'python': 2, 'knowledge_skills': 25, 'customer_service': 1, 'simulations': 3, 'mobile': 5, 'sales': 3, 'marketing': 11}

- **[382] Following Instructions v1 - UK (R1)**: FP across categories: {'personality_behavior': 6, 'testing': 7, 'data_science': 16, 'ability_aptitude': 7, 'devops': 10, 'finance': 1, 'biodata_situational_judgment': 9, 'management': 5, 'hr': 3, 'cybersecurity': 8, 'general': 20, 'frontend': 11, 'backend': 16, 'cloud': 6, 'cognitive': 1, 'sql': 3, 'java': 7, 'development_360': 23, 'python': 16, 'knowledge_skills': 16, 'simulations': 7, 'mobile': 1, 'assessment_exercises': 2, 'marketing': 2}

- **[4062] Drupal (New)**: FP across categories: {'personality_behavior': 10, 'testing': 9, 'data_science': 11, 'ability_aptitude': 1, 'devops': 1, 'biodata_situational_judgment': 4, 'management': 2, 'hr': 1, 'cybersecurity': 9, 'general': 3, 'frontend': 44, 'backend': 36, 'sql': 17, 'java': 2, 'development_360': 5, 'python': 23, 'knowledge_skills': 21, 'simulations': 1, 'mobile': 1, 'marketing': 1}

- **[4080] HTML/CSS (New)**: FP across categories: {'personality_behavior': 10, 'testing': 5, 'data_science': 3, 'ability_aptitude': 1, 'management': 2, 'cybersecurity': 4, 'general': 8, 'frontend': 55, 'backend': 29, 'cloud': 2, 'cognitive': 1, 'java': 13, 'development_360': 4, 'python': 6, 'knowledge_skills': 31, 'customer_service': 5, 'simulations': 4, 'mobile': 2, 'marketing': 1, 'personality': 1}

- **[4040] ITIL (IT Infrastructure Library) (New)**: FP across categories: {'personality_behavior': 16, 'testing': 15, 'data_science': 2, 'ability_aptitude': 2, 'devops': 36, 'biodata_situational_judgment': 4, 'management': 19, 'hr': 4, 'cybersecurity': 13, 'general': 4, 'backend': 1, 'cloud': 32, 'development_360': 14, 'python': 2, 'knowledge_skills': 10, 'customer_service': 4, 'simulations': 5, 'assessment_exercises': 1}

- **[4171] Search Engine Optimization (New)**: FP across categories: {'personality_behavior': 9, 'testing': 6, 'data_science': 19, 'ability_aptitude': 4, 'devops': 10, 'finance': 1, 'biodata_situational_judgment': 4, 'management': 13, 'hr': 3, 'cybersecurity': 6, 'general': 13, 'frontend': 8, 'backend': 12, 'cloud': 6, 'cognitive': 1, 'sql': 2, 'java': 5, 'development_360': 8, 'python': 5, 'knowledge_skills': 27, 'simulations': 7, 'mobile': 2, 'sales': 1, 'assessment_exercises': 1, 'marketing': 7}

- **[4116] Operations Management (New)**: FP across categories: {'personality_behavior': 9, 'testing': 9, 'data_science': 2, 'ability_aptitude': 10, 'devops': 21, 'biodata_situational_judgment': 6, 'management': 62, 'hr': 4, 'cybersecurity': 1, 'general': 3, 'frontend': 3, 'backend': 2, 'cloud': 6, 'cognitive': 3, 'java': 1, 'development_360': 5, 'python': 2, 'knowledge_skills': 10, 'simulations': 4, 'sales': 1, 'assessment_exercises': 1, 'marketing': 11}

- **[3941] Verify - Following Instructions**: FP across categories: {'personality_behavior': 12, 'testing': 4, 'data_science': 7, 'ability_aptitude': 7, 'devops': 11, 'finance': 1, 'biodata_situational_judgment': 10, 'management': 2, 'hr': 2, 'cybersecurity': 5, 'general': 14, 'frontend': 12, 'backend': 13, 'cloud': 6, 'cognitive': 1, 'sql': 3, 'java': 6, 'development_360': 21, 'python': 8, 'knowledge_skills': 15, 'customer_service': 1, 'simulations': 6, 'mobile': 2, 'assessment_exercises': 2, 'marketing': 3}

- **[383] Following Instructions v1 - US (R2)**: FP across categories: {'personality_behavior': 12, 'testing': 9, 'data_science': 7, 'ability_aptitude': 2, 'devops': 11, 'finance': 1, 'biodata_situational_judgment': 8, 'management': 5, 'hr': 2, 'cybersecurity': 7, 'general': 15, 'frontend': 9, 'backend': 11, 'cloud': 5, 'cognitive': 1, 'sql': 3, 'java': 3, 'development_360': 23, 'python': 8, 'knowledge_skills': 17, 'simulations': 8, 'mobile': 1, 'marketing': 1}

- **[3827] .NET Framework 4.5**: FP across categories: {'personality_behavior': 14, 'testing': 3, 'data_science': 4, 'devops': 13, 'hr': 2, 'general': 27, 'frontend': 11, 'backend': 19, 'cloud': 11, 'sql': 6, 'java': 7, 'development_360': 3, 'python': 8, 'knowledge_skills': 32, 'customer_service': 2, 'mobile': 4}

- **[4072] Front Office Management (New)**: FP across categories: {'personality_behavior': 8, 'testing': 6, 'data_science': 2, 'ability_aptitude': 8, 'devops': 8, 'finance': 1, 'biodata_situational_judgment': 6, 'management': 42, 'hr': 8, 'cybersecurity': 2, 'general': 6, 'frontend': 12, 'backend': 7, 'entry_level': 1, 'cloud': 9, 'cognitive': 8, 'development_360': 5, 'python': 2, 'knowledge_skills': 5, 'customer_service': 3, 'simulations': 1, 'sales': 1, 'assessment_exercises': 2, 'marketing': 9}

- **[4101] Desktop Support (New)**: FP across categories: {'personality_behavior': 16, 'testing': 11, 'data_science': 2, 'ability_aptitude': 5, 'devops': 14, 'biodata_situational_judgment': 4, 'management': 3, 'cybersecurity': 14, 'general': 2, 'frontend': 9, 'backend': 14, 'cloud': 5, 'cognitive': 4, 'development_360': 14, 'knowledge_skills': 22, 'customer_service': 6, 'simulations': 5, 'mobile': 4, 'assessment_exercises': 1, 'marketing': 1}

- **[4094] .NET MVC (New)**: FP across categories: {'personality_behavior': 13, 'testing': 2, 'data_science': 5, 'devops': 12, 'hr': 2, 'cybersecurity': 3, 'general': 27, 'frontend': 9, 'backend': 15, 'cloud': 9, 'sql': 5, 'java': 6, 'development_360': 3, 'python': 8, 'knowledge_skills': 31, 'mobile': 4, 'sales': 1}

- **[333] Interviewing and Hiring Concepts (U.S.)**: FP across categories: {'personality_behavior': 8, 'testing': 5, 'data_science': 10, 'ability_aptitude': 5, 'devops': 11, 'biodata_situational_judgment': 6, 'management': 24, 'hr': 8, 'cybersecurity': 5, 'general': 13, 'frontend': 6, 'backend': 5, 'entry_level': 1, 'cloud': 6, 'cognitive': 1, 'sql': 3, 'java': 3, 'development_360': 7, 'python': 4, 'knowledge_skills': 11, 'customer_service': 1, 'simulations': 3, 'mobile': 2, 'sales': 1, 'assessment_exercises': 2, 'marketing': 3}

- **[116] Software Business Analysis**: FP across categories: {'personality_behavior': 22, 'testing': 5, 'data_science': 6, 'ability_aptitude': 15, 'devops': 8, 'finance': 1, 'biodata_situational_judgment': 8, 'management': 23, 'hr': 1, 'cybersecurity': 10, 'general': 5, 'backend': 2, 'cloud': 8, 'cognitive': 1, 'sql': 1, 'java': 2, 'development_360': 9, 'python': 2, 'knowledge_skills': 19, 'customer_service': 1, 'simulations': 1, 'sales': 2, 'assessment_exercises': 2}

- **[4092] Microsoft Dynamics Development (New)**: FP across categories: {'personality_behavior': 6, 'testing': 7, 'data_science': 2, 'ability_aptitude': 2, 'devops': 21, 'biodata_situational_judgment': 5, 'management': 17, 'hr': 3, 'cybersecurity': 2, 'general': 5, 'frontend': 5, 'backend': 7, 'cloud': 29, 'cognitive': 3, 'java': 1, 'development_360': 7, 'python': 3, 'knowledge_skills': 19, 'simulations': 3, 'mobile': 2, 'sales': 3, 'marketing': 2}

- **[3974] Verify Interactive G+ Report**: FP across categories: {'personality_behavior': 13, 'data_science': 8, 'ability_aptitude': 1, 'devops': 17, 'biodata_situational_judgment': 5, 'management': 1, 'cybersecurity': 17, 'frontend': 11, 'backend': 10, 'cloud': 6, 'java': 3, 'development_360': 18, 'python': 1, 'knowledge_skills': 32, 'simulations': 2, 'mobile': 3}

- **[4099] .NET MVVM (New)**: FP across categories: {'personality_behavior': 13, 'testing': 2, 'data_science': 4, 'devops': 11, 'hr': 2, 'general': 27, 'frontend': 7, 'backend': 14, 'cloud': 13, 'sql': 2, 'java': 4, 'development_360': 3, 'python': 8, 'knowledge_skills': 30, 'mobile': 4, 'sales': 1}