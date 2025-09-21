const { themes } = require('prism-react-renderer');

const darkTheme = themes.dracula;

module.exports = {
	title: 'YuLan-OneSim',
	tagline: 'A Next Generation Social Simulator with Large Language Models',
	url: 'https://ruc-gsai.github.io',
	baseUrl: '/YuLan-OneSim/',
	favicon: '/img/favicon.png',
	organizationName: 'RUC-GSAI',
	projectName: 'YuLan-OneSim',
	staticDirectories: ['static'],
	deploymentBranch: 'gh-pages',
	scripts: [
		{
			src: 'https://buttons.github.io/buttons.js',
			async: true,
			defer: true,
		},
	],
	themeConfig: {
		navbar: {
			logo: {
				alt: 'YuLan-OneSim Logo',
				src: '/img/logo.png',
			},
			items: [
				{
					to: 'docs/overview/introduction',
					activeBasePath: 'docs',
					label: 'Docs',
					position: 'left',
				},
				{
					href: 'https://arxiv.org/abs/2505.07581',
					label: 'Paper',
					position: 'left',
				},
				{
					href: 'https://www.youtube.com/watch?v=GSW2A76FIyw',
					label: 'Video Demo',
					position: 'left',
				},
				// {
				// 	to: 'docs/overview/introduction',
				// 	label: 'About',
				// 	position: 'left',
				// },
				{
					href: 'https://github.com/RUC-GSAI/YuLan-OneSim',
					label: 'GitHub',
					position: 'right',
				},
			],
		},
		footer: {
			links: [
				{
					title: 'Documentation',
					items: [
						{
							label: 'Getting Started',
							to: '/docs/getting-started/requirements',
						},
						{
							label: 'API Reference',
							to: '/docs/api-reference/core-api',
						},
					],
				},
				{
					title: 'Community',
					items: [
						{
							label: 'GitHub',
							href: 'https://github.com/RUC-GSAI/YuLan-OneSim',
						},
						{
							label: 'Issues',
							href: 'https://github.com/RUC-GSAI/YuLan-OneSim/issues',
						},
						{
							label: 'arXiv Paper',
							href: 'https://arxiv.org/abs/2505.07581',
						},
					],
				},
			],
			copyright: 'Made with ❤️ by YuLan-OneSim Team at RUC-GSAI.',
		},
		prism: {
			theme: darkTheme,
			additionalLanguages: ['python', 'json', 'bash', 'yaml'],
		},
		colorMode: {
			defaultMode: 'light',
			disableSwitch: false,
			respectPrefersColorScheme: true,
		},
		docs: {
			sidebar: {
				autoCollapseCategories: true,
			},
		},
		trailingSlash: false,
	},
	presets: [
		[
			'@docusaurus/preset-classic',
			{
				docs: {
					sidebarPath: require.resolve('./sidebars.js'),
					sidebarCollapsible: true,
				},
				theme: {
					customCss: [
						require.resolve('./src/theme/styles.css'),
					],
				},
				blog: false,
				sitemap: {
					changefreq: 'weekly',
					priority: 0.5,
				},
			},
		],
	],
	plugins: [
		'es-text-loader',
	],
	customFields: {
		keywords: [
			'social simulation',
			'large language models',
			'multi-agent systems',
			'social science research',
			'ai simulator',
			'llm agents',
			'research platform',
		],
		image: 'img-yulan-onesim.png',
	},
};

