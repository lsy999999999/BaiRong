import React from 'react';
import useDocusaurusContext from '@docusaurus/useDocusaurusContext';
import useBaseUrl from '@docusaurus/useBaseUrl';
import Layout from '@theme/Layout';

// Simulation Dashboard component for homepage
function SimulationDashboard() {
	const [logs, setLogs] = React.useState([]);
	
	// Agent交互日志模板
	const logTemplates = [
		"JobSeeker_{id} applied to position 'Software Engineer' at Company_{cid}",
		"Employer_{id} reviewing application from JobSeeker_{cid}",
		"JobSeeker_{id} negotiating salary with Employer_{cid} - Offered: ${amount}",
		"Employer_{id} posted new position 'Data Analyst' - Skills: Python, SQL",
		"JobSeeker_{id} accepted offer from Employer_{cid}",
		"Employer_{id} sent interview invitation to JobSeeker_{cid}",
		"JobSeeker_{id} completed skills assessment - Score: {score}/100",
		"JobSeeker_{id} rejected offer from Employer_{cid}",
		"Employer_{id} updated job requirements for position 'UX Designer'",
		"JobSeeker_{id} started interview process with Company_{cid}",
		"Employer_{id} extended deadline for application to position 'Project Manager'",
		"JobSeeker_{id} submitted portfolio to Employer_{cid}",
		"Company_{id} increased hiring budget by ${amount}",
		"JobSeeker_{id} networking with Professional_{cid}",
		"Employer_{id} scheduled second interview for JobSeeker_{cid}",
		"JobSeeker_{id} updated resume with new certification",
		"Company_{id} launched employee referral program",
		"JobSeeker_{id} researching market salary for position 'DevOps Engineer'",
		"Employer_{id} conducting background check for JobSeeker_{cid}",
		"JobSeeker_{id} declined interview request from Employer_{cid}"
	];
	
	// 生成随机日志
	const generateLog = () => {
		const template = logTemplates[Math.floor(Math.random() * logTemplates.length)];
		const now = new Date();
		const timestamp = now.toLocaleString('en-US', { 
			year: 'numeric', 
			month: '2-digit', 
			day: '2-digit', 
			hour: '2-digit', 
			minute: '2-digit', 
			second: '2-digit',
			hour12: false
		});
		
		let log = template
			.replace(/{id}/g, Math.floor(Math.random() * 9999) + 1)
			.replace(/{cid}/g, Math.floor(Math.random() * 999) + 1)
			.replace(/{amount}/g, (Math.floor(Math.random() * 50) + 50) * 1000)
			.replace(/{score}/g, Math.floor(Math.random() * 40) + 60);
			
		return { timestamp, content: log, id: Date.now() + Math.random() };
	};
	
	// 实时更新逻辑
	React.useEffect(() => {
		const interval = setInterval(() => {
			// 添加新日志，带有滚动动画效果
			setLogs(prev => {
				const newLog = generateLog();
				const newLogs = [newLog, ...prev];
				return newLogs.slice(0, 15); // 增加到15条日志以适应更高的容器
			});
		}, 2500); // 2.5秒更新一次，更流畅
		
		// 初始化几条日志
		const initialLogs = Array.from({ length: 10 }, () => generateLog());
		setLogs(initialLogs);
		
		return () => clearInterval(interval);
	}, []);

	return (
		<div className="simulation-dashboard">
			{/* 顶部导航栏 */}
			<div className="dashboard-header">
				<div className="window-controls">
					<span className="control-btn red"></span>
					<span className="control-btn yellow"></span>
					<span className="control-btn green"></span>
				</div>
				<h3 className="dashboard-title">YuLan-OneSim</h3>
			</div>
			
			{/* 主要内容区域 */}
			<div className="dashboard-content">
				{/* 主状态卡片 */}
				<div className="main-status-card">
					<div className="card-header">
						<h4>Job Market Simulation</h4>
					</div>
					
					{/* 视频展示区 */}
					<div className="simulation-display">
						<video
							src="/YuLan-OneSim/img/homepage/simulation.mp4"
							autoPlay
							loop
							muted
							playsInline
							className="simulation-video"
						/>
					</div>
				</div>
			</div>
			
			{/* 底部实时日志区域 */}
			<div className="logs-section">
				<div className="logs-header">
					<span>Agent Interactions</span>
				</div>
				<div className="logs-container">
					{logs.map((log, index) => (
						<div 
							key={log.id} 
							className={`log-entry ${index === 0 ? 'log-new' : ''}`}
							style={{ 
								opacity: 1 - (index * 0.1),
								animationDelay: index === 0 ? '0s' : 'none'
							}}
						>
							<span className="log-timestamp">[{log.timestamp}]</span>
							<span className="log-content">{log.content}</span>
						</div>
					))}
				</div>
			</div>
		</div>
	);
}

export default function Home() {
	const context = useDocusaurusContext();
	const { siteConfig = {} } = context;

	// 8 research domains and scenarios data
	const researchDomains = [
		{
			domain: "Psychology",
			scenarios: ["Antisocial Personality Theory", "Attribution Theory", "Cognitive Dissonance Theory", "Conformity Behavior Model", "Emotional Contagion Model", "Metacognition Theory"]
		},
		{
			domain: "Economics",
			scenarios: ["Auction Market Dynamics", "Bank Reserves", "Cash Flow", "Collective Action Problem", "Customer Satisfaction and Loyalty Model", "Rational Choice Theory"]
		},
		{
			domain: "Communication",
			scenarios: ["Agenda Setting Theory", "Cultural Globalization", "Diffusion of Innovations", "Information Cascade and Silence", "Two Step Flow Model", "Uses and Gratifications Theory"]
		},
		{
			domain: "Law",
			scenarios: ["Case Law Model", "Court Trial Simulation", "Self Defense and Excessive Defense", "Social Contract Theory", "Tort Law and Compensation", "Unjust Enrichment", "Work Hours and Overtime in Labor Law"]
		},
		{
			domain: "Demographics",
			scenarios: ["Community Health Mobilization Theory", "Epidemic Transmission Network", "Health Belief Model", "Health Inequality", "Life Course Theory", "Reciprocal Altruism Theory", "SIR Model"]
		},
		{
			domain: "Sociology",
			scenarios: ["Cultural Capital Theory", "Norm Formation Theory", "Social Capital Theory", "Social Relations Theory", "Social Stratification Network", "Theory of Planned Behavior"]
		},
		{
			domain: "Politics",
			scenarios: ["Electoral Polarization System", "Public Opinion Polling", "Rebellion", "Selective Exposure Theory", "Simple Policy Implementation Model", "Voting"]
		},
		{
			domain: "Organization",
			scenarios: ["Decision Theory", "Hawthorne Studies", "Hierarchy of Needs", "Labor Market Matching Process", "Organizational Change and Adaptation Theory", "Scientific Management Theory"]
		}
	];

	return (
		<Layout
			title={siteConfig.title}
			description={siteConfig.tagline}
			keywords={siteConfig.customFields.keywords}
			metaImage={useBaseUrl(`img/${siteConfig.customFields.image}`)}
		>
			{/* Modern Hero Section */}
			<section className="hero-modern">
				<div className="hero-background">
					<div className="hero-gradient"></div>
					<div className="hero-particles"></div>
				</div>
				<div className="container hero-content">
					<div className="row align-items-center">
						<div className="col col--6">
							<div className="hero-text">
								<div className="hero-badge">
									<span>🚀 Next Generation Social Simulator</span>
								</div>
								<h1 className="hero-title">
									<img src="/YuLan-OneSim/img/logo.png" alt="YuLan OneSim" className="hero-logo" />
									<span className="gradient-text">YuLan-OneSim</span>
								</h1>
								<p className="hero-subtitle">
									A Next Generation Social Simulator with Large Language Models
								</p>
								<p className="hero-description">
								Reimagining Social Science with Generative Intelligence. 
								Leverage powerful LLM agents to model human behavior, explore social dynamics, and advance social science research with user-friendly simulation platform. 
								</p>
								<div className="hero-buttons">
									<a className="button-primary" href="/YuLan-OneSim/docs/getting-started/requirements">
										<span>🚀 Get Started</span>
									</a>
									<a className="button-secondary" href="https://github.com/RUC-GSAI/YuLan-OneSim">
										<span>⭐ View on GitHub</span>
									</a>
								</div>
								<div className="hero-stats">
									<div className="stat-item">
										<span className="stat-number">50+</span>
										<span className="stat-label">Default Scenarios</span>
									</div>
									<div className="stat-item">
										<span className="stat-number">100K+</span>
										<span className="stat-label">Agent Support</span>
									</div>
									<div className="stat-item">
										<span className="stat-number">8</span>
										<span className="stat-label">Research Domains</span>
									</div>
								</div>
							</div>
						</div>
						<div className="col col--6">
							<div className="hero-visual">
								<div className="hero-image-wrapper">
									<SimulationDashboard />
									<div className="hero-glow"></div>
								</div>
							</div>
						</div>
					</div>
				</div>
			</section>

			{/* Features Section */}
			<section className="features-modern">
				<div className="container">
					<div className="section-header">
						<h2 className="section-title">
							<span className="section-emoji">✨</span>
							Why Choose YuLan-OneSim
						</h2>
						<p className="section-subtitle">
							Powerful features designed for modern social science research
						</p>
					</div>
					<div className="features-grid">
						<div className="feature-card">
							<div className="feature-content">
								<div className="feature-icon-inline">
									<span>🔄</span>
									<h3>Code-free scenario construction</h3>
								</div>
								<p>Design complex simulations through natural language conversations.</p>
							</div>
						</div>
						<div className="feature-card">
							<div className="feature-content">
								<div className="feature-icon-inline">
									<span>📚</span>
									<h3>Comprehensive default scenarios</h3>
								</div>
								<p>Provide 50+ default scenarios across 8 major social science domains.</p>
							</div>
						</div>
						<div className="feature-card">
							<div className="feature-content">
								<div className="feature-icon-inline">
									<span>🧠</span>
									<h3>Evolvable simulation</h3>
								</div>
								<p>Allow automatic LLM updates based on human or machine feedback.</p>
							</div>
						</div>
						<div className="feature-card">
							<div className="feature-content">
								<div className="feature-icon-inline">
									<span>🚀</span>
									<h3>Large-scale simulation</h3>
								</div>
								<p>Distributed architecture supporting up to 100,000 agents.</p>
							</div>
						</div>
						<div className="feature-card">
							<div className="feature-content">
								<div className="feature-icon-inline">
									<span>🔍</span>
									<h3>AI social researcher</h3>
								</div>
								<p>Autonomous research capabilities from topic proposal to comprehensive report generation.</p>
							</div>
						</div>
						<div className="feature-card">
							<div className="feature-content">
								<div className="feature-icon-inline">
									<span>🎯</span>
									<h3>Flexible & User-friendly</h3>
								</div>
								<p>User-friendly interface allows arbitrary modification of scenarios, tracking and intervention in simulation processes.</p>
							</div>
						</div>
					</div>
				</div>
			</section>

			{/* Frontend Demo Section */}
			<section className="demo-modern">
				<div className="container">
					<div className="section-header">
						<h2 className="section-title">
							<span className="section-emoji">🎮</span>
							Platform Demo
						</h2>
						<p className="section-subtitle">
							Watch a comprehensive introduction to YuLan-OneSim's powerful features and user-friendly interface.
						</p>
					</div>
					<div className="demo-content" style={{ display: 'flex', justifyContent: 'center' }}>
						<div className="demo-video-wrapper" style={{ width: '100%', maxWidth: '880px' }}>
							<iframe
								style={{
									width: '100%',
									aspectRatio: '16/9',
									border: 'none',
									borderRadius: '12px',
								}}
								src="https://www.youtube.com/embed/GSW2A76FIyw"
								title="YuLan-OneSim Platform Demo"
								allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
								allowFullScreen
							></iframe>
						</div>
						{/*
						<div className="demo-features">
							<div className="demo-feature">
								<div className="demo-feature-content">
									<div className="demo-feature-icon-inline">
										<span>🖥️</span>
										<h4>User-friendly Web Interface</h4>
									</div>
									<p>Clean and modern user interface that requires no complex configuration to start simulations</p>
								</div>
							</div>
							<div className="demo-feature">
								<div className="demo-feature-content">
									<div className="demo-feature-icon-inline">
										<span>⚙️</span>
										<h4>Visual Configuration</h4>
									</div>
									<p>Easily configure model parameters and simulation environments through graphical interface</p>
								</div>
							</div>
							<div className="demo-feature">
								<div className="demo-feature-content">
									<div className="demo-feature-icon-inline">
										<span>📊</span>
										<h4>Real-time Monitoring</h4>
									</div>
									<p>View simulation progress in real-time with interactive result visualizations</p>
								</div>
							</div>
						</div>
						*/}
					</div>
				</div>
			</section>

			{/* Research Domains Section */}
			<section className="domains-modern">
				<div className="container">
					<div className="section-header">
						<h2 className="section-title">
							<span className="section-emoji">🔬</span>
							8 Major Research Domains
						</h2>
						<p className="section-subtitle">
							50+ scenarios covering major social science research areas
						</p>
					</div>
					<div className="domains-carousel">
						<div className="domains-scroll">
							{researchDomains.map((domain, index) => (
								<a key={index} href={`/YuLan-OneSim/docs/scenarios/built-in-scenarios#${domain.domain.toLowerCase()}`} className="domain-card-link">
									<div className="domain-card">
										<h3 className="domain-title">{domain.domain}</h3>
										<div className="scenarios-list">
											{domain.scenarios.map((scenario, idx) => (
												<div key={idx} className="scenario-item">
													{scenario}
												</div>
											))}
										</div>
									</div>
								</a>
							))}
						</div>
					</div>
				</div>
			</section>

			{/* CTA Section */}
			<section className="cta-modern">
				<div className="container">
					<div className="cta-content">
						<div className="cta-text">
							<h2>Ready to Transform Your Research?</h2>
							<p>Join researchers worldwide using YuLan-OneSim to advance social science understanding</p>
						</div>
						<div className="cta-buttons-inline">
							<a className="button-primary" href="/YuLan-OneSim/docs/overview/introduction">
								<span>📖 Explore Documentation</span>
							</a>
							<a className="button-secondary" href="https://www.bilibili.com/video/BV1JJKoztEc9/?share_source=copy_web&vd_source=8400639fd585f4c18394d40a3dcc0743">
								<span>🎯 Start Video Tutorial</span>
							</a>
							<a className="button-secondary" href="https://arxiv.org/abs/2505.07581">
								<span>📄 Read Paper</span>
							</a>
						</div>
						<div className="cta-footer">
							<p>Open source • MIT License • Active community support</p>
						</div>
					</div>
				</div>
			</section>
		</Layout>
	);
}
