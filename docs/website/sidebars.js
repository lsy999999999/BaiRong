module.exports = {
	docs: [
		// 1. Project Overview
		{
			type: 'category',
			label: '📋 Overview',
			collapsed: false,
			items: [
				'overview/introduction',
				'overview/architecture',
				'overview/changelog',
			],
		},
		
		// 2. Getting Started
		{
			type: 'category',
			label: '🚀 Getting Started',
			collapsed: false,
			items: [
				'getting-started/requirements',
				'getting-started/installation',
				'getting-started/first-simulation',
				'getting-started/cli-reference',
				'getting-started/web-interface',
			],
		},
		
		// 3. Core Concepts & Architecture
		{
			type: 'category',
			label: '🏗️ Architecture',
			collapsed: true,
			items: [
				'architecture/overview',
				'architecture/agent',
				'architecture/environment',
				'architecture/distributed',
				'architecture/event',
				'architecture/scenario-creation',
			],
		},
		
		// 4. Configuration Guide
		{
			type: 'category',
			label: '⚙️ Configuration',
			collapsed: true,
			items: [
				'configuration/config-structure',
				'configuration/simulation-config',
				'configuration/model-config',
				'configuration/distributed-config',
				'configuration/monitoring-database',
			],
		},
		
		// 5. Environment Development
		{
			type: 'category',
			label: '🌍 Scenarios',
			collapsed: true,
			items: [
				'scenarios/overview',
				'scenarios/scenario-structure',
				'scenarios/built-in-scenarios',
				'scenarios/custom-development',
			],
		},
		
		// 6. AI Social Researcher
		{
			type: 'category',
			label: '🔍 AI Researcher',
			collapsed: true,
			items: [
				'ai-researcher/overview',
				'ai-researcher/research-workflow',
				'ai-researcher/environment-design',
				'ai-researcher/report-generation',
				'ai-researcher/examples',
			],
		},
		
		// 7. API Reference
		{
			type: 'category',
			label: '📚 API Reference',
			collapsed: true,
			items: [
				'api-reference/core-api',
				'api-reference/agent-api',
				'api-reference/environment-api',
				'api-reference/rest-api',
				'api-reference/events-api',
			],
		},
		
		// // 8. Frontend UI
		// {
		// 	type: 'category',
		// 	label: '🎨 Frontend',
		// 	collapsed: true,
		// 	items: [
		// 		'frontend/overview',
		// 		'frontend/simulation-console',
		// 		'frontend/visualization',
		// 		'frontend/editor-features',
		// 		'frontend/customization',
		// 	],
		// },
		
		// 9. Model Tuning
		{
			type: 'category',
			label: '🧠 Model Tuning',
			collapsed: true,
			items: [
				'model-tuning/overview',
				'model-tuning/data-preparation',
				'model-tuning/tuning-process',
				'model-tuning/evaluation',
				'model-tuning/best-practices',
			],
		},
		
		// 10. Troubleshooting
		{
			type: 'category',
			label: '🔧 Troubleshooting',
			collapsed: true,
			items: [
				'troubleshooting/faq',
				'troubleshooting/community-support',
			],
		},
	],
};
