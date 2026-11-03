import { Fragment, useEffect, useState } from 'react';
import type { CSSProperties, ReactNode } from 'react';
import { useDiveState, useSQLQuery } from '@motherduck/react-sql-query';
import {
	CartesianGrid,
	Legend,
	Line,
	LineChart,
	ReferenceLine,
	ResponsiveContainer,
	Tooltip,
	XAxis,
	YAxis,
} from 'recharts';
import {
	ArrowLeft,
	ArrowRight,
	Bot,
	Cpu,
	Database,
	Eye,
	FileText,
	Flag,
	LayoutGrid,
	Lock,
	MessageSquare,
	PanelTop,
	RefreshCw,
	Shield,
	User,
	Wrench,
} from 'lucide-react';

export const REQUIRED_DATABASES = [
	{
		type: 'share',
		path: 'md:_share/dg_gaming_gloamwick_liveops_s_82cb146b_r1/936b62ca-cd54-41a6-987d-f7b64215a773',
		alias: 'gaming_gloamwick_liveops',
	},
];

// Workshop brand: sand background, ink borders with a hard shadow, sun for emphasis.
const C = {
	sand: '#f4efea',
	ink: '#383838',
	sun: '#ffde00',
	duck: '#ff9538',
	garden: '#087f72',
	sky: '#6fc2ff',
	coral: '#ff7169',
	muted: '#6a6a6a',
	white: '#ffffff',
};
const MONO = 'ui-monospace, SFMono-Regular, Menlo, Consolas, monospace';
const box = (bg: string = C.white) => ({
	background: bg,
	border: `2px solid ${C.ink}`,
	boxShadow: `-6px 6px 0 ${C.ink}`,
});
const N = (v: unknown): number => (v == null ? 0 : Number(v));

type Slide = {
	id: string;
	section: string;
	title: string;
	notes: string;
	render: (ctx: { reveal: boolean; go: (id: string) => void }) => JSX.Element;
};

function Kicker({ children }: { children: ReactNode }) {
	return (
		<span
			className="text-xs uppercase"
			style={{ fontFamily: MONO, letterSpacing: 2, color: C.garden }}
		>
			{children}
		</span>
	);
}

function Card({
	children,
	bg,
	className = '',
	style = {},
}: {
	children: ReactNode;
	bg?: string;
	className?: string;
	style?: CSSProperties;
}) {
	return (
		<div className={'p-3 ' + className} style={{ ...box(bg), ...style }}>
			{children}
		</div>
	);
}

function Guess({ show, children }: { show: boolean; children: ReactNode }) {
	return show ? (
		<>{children}</>
	) : (
		<span style={{ fontFamily: MONO, color: C.muted }}>your guess?</span>
	);
}

function Steps({
	minutes,
	status,
	steps,
	done,
}: {
	minutes: number;
	status: string;
	steps: string[];
	done: string;
}) {
	const tested = status.startsWith('tested');
	return (
		<div className="p-4" style={{ border: `3px dashed ${C.ink}` }}>
			<div className="flex items-center gap-4 mb-3">
				<span className="text-3xl" style={{ fontFamily: MONO }}>
					{minutes} MIN
				</span>
				<span
					className="text-xs px-2 py-1 uppercase"
					style={{
						fontFamily: MONO,
						color: C.white,
						background: tested ? C.garden : C.coral,
					}}
				>
					{status}
				</span>
			</div>
			<ol className="space-y-1 text-sm" style={{ paddingLeft: 20, listStyle: 'decimal' }}>
				{steps.map((s) => (
					<li key={s}>{s}</li>
				))}
			</ol>
			<div className="mt-3 p-2 flex items-center gap-2 text-sm" style={box(C.sun)}>
				<Flag size={16} /> <b>DONE WHEN</b> {done}
			</div>
		</div>
	);
}

function Table({ head, rows, strong }: { head: string[]; rows: string[][]; strong?: number }) {
	return (
		<table className="w-full text-sm" style={{ ...box(), borderCollapse: 'collapse' }}>
			<thead>
				<tr style={{ background: '#ece4dc' }}>
					{head.map((h) => (
						<th
							key={h}
							className="text-left p-2 text-xs uppercase"
							style={{ fontFamily: MONO, borderBottom: `2px solid ${C.ink}` }}
						>
							{h}
						</th>
					))}
				</tr>
			</thead>
			<tbody>
				{rows.map((r, i) => (
					<tr
						key={r[0]}
						style={{ background: i === strong ? C.sun : undefined, borderTop: '1px solid #ddd' }}
					>
						{r.map((c, j) => (
							<td key={j} className="p-2">
								{c}
							</td>
						))}
					</tr>
				))}
			</tbody>
		</table>
	);
}

// Live slide 1: weekly D7 retention by platform, with the boss rework marked.
function RetentionChart() {
	const q = useSQLQuery(`
    SELECT strftime(date_trunc('week', metric_date), '%Y-%m-%d') AS week,
      100.0 * sum(d7_retained) FILTER (WHERE platform = 'android')
        / nullif(sum(installs) FILTER (WHERE platform = 'android'), 0) AS android,
      100.0 * sum(d7_retained) FILTER (WHERE platform = 'ios')
        / nullif(sum(installs) FILTER (WHERE platform = 'ios'), 0) AS ios
    FROM "gaming_gloamwick_liveops"."main"."daily_player_metrics"
    WHERE d7_matured
    GROUP BY 1
    ORDER BY 1
  `);
	const rows = (Array.isArray(q.data) ? q.data : []).map((r) => ({
		week: String(r.week),
		android: Math.round(N(r.android) * 10) / 10,
		ios: Math.round(N(r.ios) * 10) / 10,
	}));
	if (q.isLoading)
		return <div className="animate-pulse rounded bg-gray-200" style={{ height: 260 }} />;
	if (q.isError) return <p role="alert">{String(q.error)}</p>;
	return (
		<ResponsiveContainer width="100%" height={260}>
			<LineChart data={rows} margin={{ top: 20, right: 10 }}>
				<CartesianGrid strokeDasharray="3 3" stroke="#ddd" />
				<XAxis dataKey="week" fontSize={11} minTickGap={40} />
				<YAxis fontSize={11} domain={[8, 20]} tickFormatter={(v) => `${v}%`} />
				<Tooltip formatter={(v) => `${v}%`} />
				<Legend />
				<ReferenceLine x="2025-04-07" stroke={C.coral} strokeDasharray="4 4" label={{ value: 'boss rework', fontSize: 11, position: 'top' }} />
				<Line type="linear" dataKey="android" name="Android D7 %" stroke={C.duck} strokeWidth={2} dot={false} />
				<Line type="linear" dataKey="ios" name="iOS D7 %" stroke="#0777b3" strokeWidth={2} dot={false} />
			</LineChart>
		</ResponsiveContainer>
	);
}

// Live slide 2: 14 days before and after the two changes that moved something.
function BeforeAfter() {
	const q = useSQLQuery(`
    SELECT e.event_name, strftime(e.start_date, '%Y-%m-%d') AS start_day, m.platform,
      CASE WHEN m.metric_date < e.start_date THEN 'before' ELSE 'after' END AS period,
      round(100.0 * sum(d7_retained) FILTER (WHERE d7_matured)
        / nullif(sum(installs) FILTER (WHERE d7_matured), 0), 2) AS d7,
      round((sum(iap_gross_cents) + sum(ad_revenue_millicents) / 1000.0) / sum(dau), 2) AS arpdau_cents
    FROM "gaming_gloamwick_liveops"."main"."live_ops_events" e
    JOIN "gaming_gloamwick_liveops"."main"."daily_player_metrics" m
      ON m.metric_date >= e.start_date - 14 AND m.metric_date < e.start_date + 14
    WHERE e.event_name IN ('level12_boss_rework', 'rewarded_chest_video')
    GROUP BY ALL
    ORDER BY 2, 3, 4 DESC
  `);
	const rows = Array.isArray(q.data) ? q.data : [];
	const pick = (ev: string, pf: string, per: string) =>
		rows.find((r) => r.event_name === ev && r.platform === pf && r.period === per);
	const cell = (ev: string, pf: string, col: 'd7' | 'arpdau_cents', unit: string) => {
		const b = pick(ev, pf, 'before');
		const a = pick(ev, pf, 'after');
		return b && a ? `${N(b[col]).toFixed(2)}${unit} → ${N(a[col]).toFixed(2)}${unit}` : '';
	};
	if (q.isLoading)
		return (
			<div className="animate-pulse space-y-2">
				<div className="h-6 rounded bg-gray-200" />
				<div className="h-6 rounded bg-gray-200" />
				<div className="h-6 rounded bg-gray-200" />
			</div>
		);
	if (q.isError) return <p role="alert">{String(q.error)}</p>;
	const out: string[][] = [];
	for (const ev of ['level12_boss_rework', 'rewarded_chest_video'])
		for (const pf of ['android', 'ios'])
			out.push([ev, pf, cell(ev, pf, 'd7', '%'), cell(ev, pf, 'arpdau_cents', '¢')]);
	return <Table head={['Change', 'Platform', 'D7 retention', 'ARPDAU']} rows={out} />;
}

const LEVELS: [string, string, string, string[]][] = [
	['l1', '1', 'Local', ['Claude Code', 'managed', '*DuckDB CLI + skill', '*your laptop', 'you']],
	['l2', '2', 'MotherDuck', ['Claude Code', 'managed', '*MotherDuck MCP + skill', '*MotherDuck', '*anyone you share with']],
	['l3', '3', 'Your tools', ['Claude Code', 'managed', '*your MCP server', 'MotherDuck', '*your users']],
	['l4', '4', 'Your agent', ['*your loop', '*your key, any model', 'your MCP server', 'MotherDuck', '*anyone with the link']],
];

const SLIDES: Slide[] = [
	{
		id: 'hero',
		section: 'MOTHERDUCK WORKSHOP · 90 MIN · HANDS-ON',
		title: '',
		notes: 'Draft Dive version of the workshop deck. Arrows or the buttons move between slides, R reveals guess slides, N shows notes. Two slides query the Gloamwick share live.',
		render: () => (
			<div className="flex flex-col justify-center h-full">
				<h1 className="text-6xl" style={{ fontFamily: MONO, lineHeight: 1.05, letterSpacing: -1 }}>
					THE NEXT
					<br />
					DATA STACK
					<br />
					HAS NO UI
				</h1>
				<p className="mt-6 text-lg">Build an analytics agent end to end, and see what each piece needs.</p>
				<p className="mt-4 text-sm" style={{ fontFamily: MONO, color: C.garden }}>
					Mehdi Ouazza · Jacob Matson
				</p>
			</div>
		),
	},
	{
		id: 'agenda',
		section: '00 · TODAY',
		title: 'Two ideas, then four levels',
		notes: 'Click a tile to jump. Chapters 1 and 2 give the vocabulary. Then four levels, each with a hands-on, where one more part of the agent becomes yours.',
		render: ({ go }) => {
			const tiles: [string, string, string, string, JSX.Element][] = [
				['agent', '01', 'The agent', 'Loop · tools · skills · harness', <RefreshCw size={28} />],
				['job', '02', 'The analytics job', 'Six tasks · the stack with no UI', <LayoutGrid size={28} />],
				['l1', 'L1', 'Local', 'DuckDB · a skill · a local dashboard', <PanelTop size={28} />],
				['l2', 'L2', 'MotherDuck', 'Remote MCP · Guides · Dives · Flights', <Database size={28} />],
				['l3', 'L3', 'Your tools', 'Your MCP server around MotherDuck', <Wrench size={28} />],
				['l4', 'L4', 'Your agent', 'Your loop · your model · your link', <Cpu size={28} />],
			];
			return (
				<div className="grid grid-cols-3 gap-4">
					{tiles.map(([id, n, t, f, icon]) => (
						<button key={id} onClick={() => go(id)} className="text-left p-3" style={{ borderTop: `1px solid ${C.ink}40`, cursor: 'pointer' }}>
							<div className="flex justify-between">
								<span className="text-3xl" style={{ fontFamily: MONO, color: C.garden }}>
									{n}
								</span>
								{icon}
							</div>
							<div className="text-xl mt-2" style={{ fontFamily: MONO }}>
								{t}
							</div>
							<div className="text-sm" style={{ color: C.muted }}>
								{f}
							</div>
						</button>
					))}
				</div>
			);
		},
	},
	{
		id: 'solved',
		section: '00 · WHY THIS WORKSHOP',
		title: 'Text to SQL is solved',
		notes: 'Every model in the room writes valid SQL. The hard part is the definition: which rows count, which units, which days.',
		render: () => (
			<div className="flex items-center h-full">
				<p className="text-3xl" style={{ fontFamily: MONO }}>
					Knowing what your business means by “revenue” is not.
				</p>
			</div>
		),
	},
	{
		id: 'agent',
		section: '01 · THE AGENT · GUESS',
		title: 'Five definitions. What do they share?',
		notes: 'Read two, ask the room, press R. Quotes checked against the source pages on 2026-11-02.',
		render: ({ reveal }) => {
			const q: [string, string, string][] = [
				['SIMON WILLISON · 2025', 'An LLM agent runs [tools] in a [loop] to achieve a [goal].', 'https://simonwillison.net/2025/Sep/18/agents/'],
				['ANTHROPIC · 2024', 'Systems where LLMs [dynamically direct] their own processes and [tool] usage.', 'https://www.anthropic.com/engineering/building-effective-agents'],
				['OPENAI · 2025', 'An agent consists of three core components: [model], [tools], [instructions].', 'https://cdn.openai.com/business-guides-and-resources/a-practical-guide-to-building-agents.pdf'],
				['LANGCHAIN · 2026', 'A system that uses a large language model to [decide the control flow] of an application.', 'https://www.langchain.com/blog/what-is-an-agent'],
				['HUGGING FACE', 'Programs where LLM outputs [control the workflow].', 'https://huggingface.co/docs/smolagents/conceptual_guides/intro_agents'],
			];
			return (
				<div className="grid grid-cols-3 gap-4">
					{q.map(([who, text, url]) => (
						<a key={who} href={url} target="_blank" rel="noopener noreferrer" className="block p-3" style={box()}>
							<Kicker>{who} ↗</Kicker>
							<p className="mt-2 text-sm">
								{text.split(/(\[[^\]]+\])/).map((t, i) =>
									t.startsWith('[') ? (
										<span key={i} style={{ background: reveal ? C.sun : 'transparent' }}>
											{t.slice(1, -1)}
										</span>
									) : (
										<span key={i}>{t}</span>
									),
								)}
							</p>
						</a>
					))}
					<div className="p-3" style={{ ...box(C.sun), visibility: reveal ? 'visible' : 'hidden' }}>
						<Kicker>WHAT THEY SHARE</Kicker>
						<p className="mt-2 text-sm">The model decides the next step, acts through tools, and loops until the goal is met.</p>
					</div>
				</div>
			);
		},
	},
	{
		id: 'spectrum',
		section: '01 · THE AGENT',
		title: 'Chatbot, workflow, agent',
		notes: 'Who decides the next step? Anthropic: workflows orchestrate LLMs through predefined code paths, agents let the LLM direct its own process and tool use.',
		render: () => (
			<div>
				<div className="grid grid-cols-3 gap-4">
					{[
						['CHATBOT', 'You', 'One model call. You do the next step yourself.'],
						['WORKFLOW', 'Your code', 'Fixed steps you wrote. The model fills in some.'],
						['AGENT', 'The model', 'It picks the next step, calls a tool, reads the result, loops.'],
					].map(([k, who, what], i) => (
						<Card key={k} bg={i === 2 ? C.sun : C.white}>
							<Kicker>{k}</Kicker>
							<div className="text-2xl mt-2" style={{ fontFamily: MONO }}>
								{who}
							</div>
							<p className="text-sm mt-2">{what}</p>
						</Card>
					))}
				</div>
				<p className="text-center mt-6">Who decides the next step?</p>
			</div>
		),
	},
	{
		id: 'loop',
		section: '01 · THE AGENT',
		title: 'The loop',
		notes: 'Claude Agent SDK: gather context, take action, verify work, repeat. ReAct (Yao et al., 2022) is the research origin. It stops when the model answers without asking for a tool.',
		render: () => {
			const st: [JSX.Element, string, string][] = [
				[<PanelTop size={22} />, 'GATHER CONTEXT', 'prompt, guide, last results'],
				[<Cpu size={22} />, 'DECIDE', 'the model writes a tool call'],
				[<Wrench size={22} />, 'ACT', 'the harness runs it'],
				[<Eye size={22} />, 'OBSERVE', 'the result goes back in'],
			];
			return (
				<div className="space-y-4">
					<div className="flex items-center gap-3 p-3" style={{ border: `2px dashed ${C.ink}` }}>
						<User size={22} />
						<Kicker>GOAL</Kicker>
						<span className="text-sm">“Which weekdays lose money to waste?”</span>
					</div>
					<div className="grid gap-2 items-center" style={{ gridTemplateColumns: '1fr 24px 1fr 24px 1fr 24px 1fr' }}>
						{st.map(([icon, n, w], i) => (
							<Fragment key={n}>
								<Card bg={i === 1 ? C.sun : C.white} className="text-center">
									<div className="flex justify-center">{icon}</div>
									<div className="text-sm mt-1" style={{ fontFamily: MONO }}>
										{n}
									</div>
									<div className="text-xs" style={{ color: i === 1 ? C.ink : C.muted }}>
										{w}
									</div>
								</Card>
								{i < 3 && <ArrowRight size={18} />}
							</Fragment>
						))}
					</div>
					<div className="flex items-center justify-between">
						<span className="flex items-center gap-2 text-sm" style={{ fontFamily: MONO, color: C.garden }}>
							<RefreshCw size={18} /> back to gather context, until…
						</span>
						<div className="flex items-center gap-2 p-3" style={box(C.sun)}>
							<Flag size={20} />
							<Kicker>DONE</Kicker>
							<span className="text-sm">it answers with no tool call</span>
						</div>
					</div>
				</div>
			);
		},
	},
	{
		id: 'anatomy',
		section: '01 · THE AGENT',
		title: 'The parts of an agent',
		notes: 'OpenAI: model, tools, instructions. LangChain: agent = model + harness, where the harness is every piece of code, configuration and execution logic that is not the model.',
		render: () => (
			<div className="flex items-center gap-3">
				<div className="w-28 text-center text-sm">
					<div className="flex justify-center">
						<User size={36} />
					</div>
					<b>Human</b>
					<div style={{ color: C.muted }}>chat, terminal, IDE</div>
				</div>
				<span>⇄</span>
				<div className="flex-1 p-3" style={{ ...box('#fffaf0'), borderWidth: 3 }}>
					<div className="flex items-center gap-2 mb-3 text-xs" style={{ fontFamily: MONO, color: C.garden }}>
						<Shield size={16} /> HARNESS · the program around the loop
					</div>
					<div className="flex items-center gap-2">
						<div className="space-y-2">
							<Card className="text-center text-xs w-36" style={{ boxShadow: 'none' }}>
								<FileText size={18} className="mx-auto" />
								<b>Instructions</b>
								<div>system prompt, AGENTS.md, skills</div>
							</Card>
							<Card className="text-center text-xs w-36" style={{ boxShadow: 'none' }}>
								<PanelTop size={18} className="mx-auto" />
								<b>Context</b>
								<div>everything it sees this turn</div>
							</Card>
						</div>
						<ArrowRight size={18} />
						<Card bg={C.sun} className="text-center text-xs w-32" style={{ boxShadow: 'none' }}>
							<Cpu size={22} className="mx-auto" />
							<b>Model</b>
							<div>picks the next step</div>
						</Card>
						<div className="text-xs" style={{ fontFamily: MONO }}>
							call →
							<br />← result
						</div>
						<Card className="text-center text-xs w-32" style={{ boxShadow: 'none' }}>
							<Wrench size={18} className="mx-auto" />
							<b>Tools</b>
							<div>name, description, schema</div>
						</Card>
					</div>
					<div className="flex flex-wrap gap-2 mt-3 pt-2 text-xs" style={{ borderTop: '2px dashed #3838384d', fontFamily: MONO }}>
						{['permissions', 'hooks', 'sandbox', 'memory', 'compaction', 'subagents'].map((r) => (
							<span key={r} className="px-2" style={{ border: `1px solid ${C.ink}`, background: C.white }}>
								{r}
							</span>
						))}
					</div>
				</div>
				<span>⇄</span>
				<div className="w-28 text-center text-sm">
					<div className="flex justify-center">
						<Database size={36} />
					</div>
					<b>Environment</b>
					<div style={{ color: C.muted }}>MotherDuck, through MCP</div>
				</div>
			</div>
		),
	},
	{
		id: 'levels',
		section: '01 · THE AGENT',
		title: 'Four levels. One more part becomes yours.',
		notes: 'Yellow is new at that level. Click a row to jump to that level.',
		render: ({ go }) => (
			<div>
				<div className="grid gap-2 text-xs" style={{ gridTemplateColumns: '130px repeat(5, 1fr)', fontFamily: MONO, color: C.garden }}>
					<span />
					{['Harness', 'Model', 'Tools', 'Data + compute', 'Who can use it'].map((h) => (
						<span key={h}>{h}</span>
					))}
				</div>
				{LEVELS.map(([id, n, name, cells]) => (
					<button key={id} onClick={() => go(id)} className="grid gap-2 w-full py-2 items-center text-left" style={{ gridTemplateColumns: '130px repeat(5, 1fr)', borderTop: `1px solid ${C.ink}30`, cursor: 'pointer' }}>
						<span className="text-lg" style={{ fontFamily: MONO }}>
							<b>{n}</b> {name}
						</span>
						{cells.map((c, i) =>
							c.startsWith('*') ? (
								<span key={i} className="p-2 text-xs" style={{ background: C.sun, border: `2px solid ${C.ink}`, fontWeight: 600 }}>
									{c.slice(1)}
								</span>
							) : (
								<span key={i} className="p-2 text-xs" style={{ border: '2px solid #38383830', color: '#777' }}>
									{c}
								</span>
							),
						)}
					</button>
				))}
			</div>
		),
	},
	{
		id: 'job',
		section: '02 · THE ANALYTICS JOB · GUESS',
		title: 'Six tasks. Guess the MotherDuck feature.',
		notes: 'Let the room shout a guess for each box, then press R.',
		render: ({ reveal }) => (
			<div>
				<div className="grid grid-cols-5 gap-3">
					{[
						['Pipelines', 'ingest and transform', 'Flights'],
						['Data apps', 'dashboards, small tools', 'Dives'],
						['Context', 'what the data means', 'Guides'],
						['Storage', 'where the data lives', 'MotherDuck · DuckLake · DuckDB'],
						['Permissions', 'what it can see and break', 'Ducklings · shares · secure views'],
					].map(([t, w, md]) => (
						<Card key={t}>
							<div className="text-base" style={{ fontFamily: MONO }}>
								{t}
							</div>
							<div className="text-xs" style={{ color: C.muted }}>
								{w}
							</div>
							<div className="text-sm mt-3" style={{ color: C.garden, fontWeight: 600 }}>
								<Guess show={reveal}>{md}</Guess>
							</div>
						</Card>
					))}
				</div>
				<Card bg={C.sun} className="mt-4 flex gap-4 items-center">
					<span style={{ fontFamily: MONO }}>Observability</span>
					<span className="text-xs">covers all of the above</span>
					<span className="text-sm ml-auto" style={{ fontWeight: 600 }}>
						<Guess show={reveal}>Flight Explainer · query history · traces in MotherDuck</Guess>
					</span>
				</Card>
			</div>
		),
	},
	{
		id: 'no-ui',
		section: '02 · THE NEXT DATA STACK HAS NO UI · GUESS',
		title: 'When an agent builds, which UIs survive?',
		notes: 'Each layer of the modern data stack ships a UI to build and a UI to watch. Building moves to chat. The watch UIs stay, and MotherDuck serves them as MCP apps.',
		render: ({ reveal }) => (
			<div className="grid grid-cols-2 gap-6">
				<Card>
					<Kicker>UI TO BUILD</Kicker>
					<p className="text-sm mt-2">connector screens, model editors, DAG editors, dashboard editors</p>
					<div className="mt-3 flex items-center gap-2 text-lg" style={{ fontFamily: MONO }}>
						<MessageSquare size={20} />
						<Guess show={reveal}>chat</Guess>
					</div>
				</Card>
				<Card bg={C.sun}>
					<Kicker>UI TO WATCH</Kicker>
					<ul className="text-sm mt-2 space-y-1">
						<li>
							Dashboards: <Guess show={reveal}>Dive viewer (view_dive)</Guess>
						</li>
						<li>
							Pipeline runs: <Guess show={reveal}>Flight Explainer (view_flight_run)</Guess>
						</li>
						<li>
							Agent traces: <Guess show={reveal}>a traces table and a Dive</Guess>
						</li>
					</ul>
				</Card>
			</div>
		),
	},
	{
		id: 'l1',
		section: 'LEVEL 1 · LOCAL',
		title: 'Level 1 · Local',
		notes: 'Harness and model are rented. You own one skill file and the data on your disk.',
		render: () => <p className="text-2xl">DuckDB on your laptop, a managed agent, one skill file.</p>,
	},
	{
		id: 'ho1',
		section: 'LEVEL 1 · HANDS-ON',
		title: 'Hands-on 1: a local analytics agent',
		notes: 'Tested 2026-11-02 with Claude Code on the OpenRouter key: 16 turns, 3.4 min, $0.38, working dashboard.html.',
		render: () => (
			<Steps
				minutes={10}
				status="tested 2026-11-02"
				steps={[
					'Save the skill file in your project.',
					'Ask the agent to load your company’s Parquet from S3 into a local DuckDB file.',
					'Ask for one clean table that answers your question.',
					'Ask your question. Note the number and the SQL.',
					'Ask for a dashboard: one HTML file you open locally.',
				]}
				done="dashboard.html opens on your laptop and shows your answer."
			/>
		),
	},
	{
		id: 'diy',
		section: 'LEVEL 1 · LOCAL',
		title: 'To share it, you build all of this',
		notes: 'The moment a teammate or another agent needs the answer, someone has to run every one of these boxes.',
		render: () => (
			<div className="grid grid-cols-4 gap-3">
				{[
					['Storage', 'durable, shared', C.sky],
					['Compute', 'isolates each user', C.duck],
					['Identity', 'users, agents, tokens', C.duck],
					['Access', 'who sees which rows', C.duck],
					['Context', 'what the data means', C.duck],
					['Pipelines', 'scheduled ingest', C.duck],
					['Apps', 'dashboards people open', C.garden],
					['Observability', 'what ran, who asked', C.duck],
				].map(([t, w, c]) => (
					<div key={t} className="p-3 rounded" style={{ background: C.white, borderTop: `5px solid ${c}`, border: '1px solid #3838382a', borderTopWidth: 5, borderTopColor: c, minHeight: 90 }}>
						<div className="uppercase" style={{ fontFamily: MONO }}>
							{t}
						</div>
						<div className="text-xs" style={{ color: C.muted }}>
							{w}
						</div>
					</div>
				))}
			</div>
		),
	},
	{
		id: 'md',
		section: 'LEVEL 2 · MOTHERDUCK',
		title: 'MotherDuck runs these boxes',
		notes: 'Clients reach MotherDuck through MCP or SQL. In the middle, the parts this workshop uses.',
		render: () => (
			<div className="grid gap-3 items-center" style={{ gridTemplateColumns: '1fr 40px 1.3fr 40px 1fr' }}>
				<div className="space-y-2">
					<Kicker>CLIENTS</Kicker>
					{['Any MCP client', 'DuckDB CLI and SDKs', 'MotherDuck UI'].map((c) => (
						<div key={c} className="p-2 text-sm rounded" style={{ background: C.white, borderLeft: `5px solid ${C.garden}` }}>
							{c}
						</div>
					))}
				</div>
				<span className="text-center">⇄</span>
				<div className="space-y-2">
					<Kicker>MOTHERDUCK</Kicker>
					{[
						['Identity and access', 'service accounts · tokens · shares · secure views'],
						['Ducklings', 'compute per user and per agent'],
						['Guides', 'context next to the data'],
						['Flights', 'Python pipelines'],
						['Dives', 'data apps, also as MCP apps'],
						['Storage + DuckLake', 'durable · shared · one copy'],
					].map(([t, w]) => (
						<div key={t} className="p-2 text-sm rounded" style={{ background: '#fffbe0', borderLeft: `5px solid ${C.duck}` }}>
							<b>{t}</b> <span className="text-xs" style={{ color: C.muted }}>{w}</span>
						</div>
					))}
				</div>
				<span className="text-center">⇄</span>
				<div className="space-y-2">
					<Kicker>EXTERNAL</Kicker>
					{['S3 · GCS · Azure', 'Databases', 'DuckLake on your bucket'].map((c) => (
						<div key={c} className="p-2 text-sm rounded" style={{ background: C.white, borderLeft: `5px solid ${C.sky}` }}>
							{c}
						</div>
					))}
				</div>
			</div>
		),
	},
	{
		id: 'l2',
		section: 'LEVEL 2 · MOTHERDUCK',
		title: 'Level 2 · MotherDuck',
		notes: 'Context, data apps, pipelines and access all show up here, because sharing is what makes them necessary.',
		render: () => <p className="text-2xl">Same agent, remote compute and dashboards. Now anyone can query.</p>,
	},
	{
		id: 'live-retention',
		section: 'LEVEL 2 · LIVE FROM THE SHARE',
		title: 'Gloamwick: weekly D7 retention by platform',
		notes: 'This slide queries the Gloamwick duckgen share live. The level 12 boss rework (2025-04-10) cuts Android D7 retention. iOS stays flat. Cohorts are grouped by install week.',
		render: () => <RetentionChart />,
	},
	{
		id: 'live-before-after',
		section: 'LEVEL 2 · LIVE FROM THE SHARE',
		title: '14 days before and after',
		notes: 'Same share, live. Every level of the workshop found these two changes. ARPDAU = (IAP gross + ad revenue) / DAU, in cents. D7 = retained on day 7 / installs, matured cohorts only.',
		render: () => <BeforeAfter />,
	},
	{
		id: 'rules',
		section: 'LEVEL 2 · PERMISSIONS',
		title: 'Where to put a rule',
		notes: 'Weakest to strongest. Guides for correctness, the database for safety.',
		render: () => (
			<div className="grid grid-cols-4 gap-3 items-end">
				{[
					['01', 'Prompt', 'The model can ignore it.'],
					['02', 'Guide', 'Helps correctness, blocks nothing.'],
					['03', 'Harness', 'The app blocks the call.'],
					['04', 'Database', 'Token, share, secure view. Holds for every client.'],
				].map(([n, t, w], i) => (
					<Card key={n} bg={i === 3 ? C.sun : C.white} style={{ marginBottom: (3 - i) * 30 }}>
						<span className="text-2xl" style={{ fontFamily: MONO, color: C.garden }}>
							{n}
						</span>
						<div className="text-lg" style={{ fontFamily: MONO }}>
							{t}
						</div>
						<p className="text-xs mt-1">{w}</p>
					</Card>
				))}
			</div>
		),
	},
	{
		id: 'ho2',
		section: 'LEVEL 2 · HANDS-ON',
		title: 'Hands-on 2: move it to MotherDuck',
		notes: 'Tested 2026-11-02 through the remote MCP: 18 turns, 67 s, $0.22. The Flight stretch is not tested yet.',
		render: () => (
			<Steps
				minutes={12}
				status="tested 2026-11-02"
				steps={[
					'Add the MotherDuck remote MCP server to your agent.',
					'Attach your company’s share and ask your question again.',
					'Write a guide with create_guide. Start a fresh session and ask again.',
					'Save your dashboard as a Dive and send the link to your neighbor.',
					'Stretch: turn the load step into a Flight.',
				]}
				done="your neighbor opens your Dive."
			/>
		),
	},
	{
		id: 'l3',
		section: 'LEVEL 3 · YOUR TOOLS',
		title: 'Own the tool surface',
		notes: 'From the MotherDuck white-label MCP guide. Forward a small set of tools, rename them, add your own, log the question, keep the token on the server.',
		render: () => (
			<div className="flex items-center gap-3">
				<div className="w-32 text-center text-sm">
					<Bot size={32} className="mx-auto" />
					<b>AI client</b>
				</div>
				<ArrowRight />
				<Card bg={C.sun} className="flex-1">
					<Kicker>YOUR MCP SERVER · FASTMCP</Kicker>
					<ul className="text-sm mt-2 space-y-1" style={{ listStyle: 'disc', paddingLeft: 18 }}>
						<li>forwards only the tools you pick</li>
						<li>your names, descriptions and instructions</li>
						<li>your own tools, like live_ops_impact</li>
						<li>a required question, logged with the SQL</li>
						<li>keeps the token, never shows it</li>
					</ul>
				</Card>
				<ArrowRight />
				<div className="w-36 text-center text-sm">
					<Database size={32} className="mx-auto" />
					<b>MotherDuck MCP</b>
					<div className="text-xs" style={{ color: C.muted }}>
						one service account per tenant
					</div>
				</div>
			</div>
		),
	},
	{
		id: 'ho3',
		section: 'LEVEL 3 · HANDS-ON',
		title: 'Hands-on 3: your own MCP server',
		notes: 'Tested 2026-11-02: 5 turns, 28 s, $0.07, because the domain tool carries the SQL.',
		render: () => (
			<Steps
				minutes={10}
				status="tested 2026-11-02"
				steps={[
					'Run the starter: uv run server.py.',
					'Rewrite the tool descriptions for your company.',
					'Add one domain tool that wraps the SQL for your question.',
					'Make question a required argument and log it.',
					'Point your agent at your server instead of MotherDuck’s.',
				]}
				done="your agent answers with your tools only, and the log shows the question."
			/>
		),
	},
	{
		id: 'l4',
		section: 'LEVEL 4 · YOUR AGENT',
		title: 'The whole agent, really',
		notes: 'The core of exercises/4-custom-agent/agent.py, tested with Gemini 3.8 Flash. No permissions, no hooks, no memory: that is the harness you now own.',
		render: () => (
			<pre className="p-4 text-sm" style={{ ...box('#2b2b2b'), color: '#f4efea', fontFamily: MONO, whiteSpace: 'pre' }}>
				{`messages = [system, question]
for step in range(MAX_STEPS):
    reply = model(messages, tools)        # any OpenRouter model
    messages += [reply]
    if not reply.tool_calls:
        return reply.content
    for call in reply.tool_calls:
        result = mcp.call_tool(call.name, call.args)   # your MCP server
        messages += [tool_result(call.id, result)]`}
			</pre>
		),
	},
	{
		id: 'ho4',
		section: 'LEVEL 4 · HANDS-ON',
		title: 'Hands-on 4: ship your agent',
		notes: 'The loop is tested. The generator around it is not built yet.',
		render: () => (
			<Steps
				minutes={10}
				status="loop tested · generator to build"
				steps={[
					'Open the generator and paste the workshop key once.',
					'Pick a model, your tools, the step cap and who the agent runs as.',
					'Deploy and get your link.',
					'Red team your neighbor.',
					'Open the Dive over the whole room’s traces.',
				]}
				done="you have a link anyone can use."
			/>
		),
	},
	{
		id: 'runs',
		section: 'WRAP',
		title: 'One question, four levels',
		notes: 'Measured on 2026-11-02, one run each, same question on Gloamwick Studios. An illustration, not a benchmark.',
		render: () => (
			<div>
				<Table
					head={['Level', 'Harness · model', 'Tools', 'Turns', 'Time', 'Cost']}
					strong={2}
					rows={[
						['1 · Local', 'Claude Code · Sonnet 5.5', 'DuckDB CLI + skill', '16', '3.4 min', '$0.38'],
						['2 · MotherDuck', 'Claude Code · Sonnet 5.5', 'MotherDuck MCP + skill', '18', '67 s', '$0.22'],
						['3 · Your tools', 'Claude Code · Sonnet 5.5', 'your MCP server', '5', '28 s', '$0.07'],
						['4 · Your agent', 'your loop · Gemini 3.8 Flash', 'your MCP server', '5 steps', '62 s', 'not measured'],
					]}
				/>
				<p className="text-center text-sm mt-4">Same finding every time. The guide from level 2 gave the level 4 model the same numbers.</p>
			</div>
		),
	},
	{
		id: 'refs',
		section: 'WRAP',
		title: 'References',
		notes: 'Every definition in chapter 1 comes from these.',
		render: () => (
			<div className="grid grid-cols-2 gap-x-6 gap-y-1 text-sm">
				{[
					['Anthropic', 'Building effective agents', 'https://www.anthropic.com/engineering/building-effective-agents'],
					['OpenAI', 'A practical guide to building agents', 'https://cdn.openai.com/business-guides-and-resources/a-practical-guide-to-building-agents.pdf'],
					['Simon Willison', 'Agents: tools in a loop', 'https://simonwillison.net/2025/Sep/18/agents/'],
					['LangChain', 'The anatomy of an agent harness', 'https://www.langchain.com/blog/the-anatomy-of-an-agent-harness'],
					['Yao et al.', 'ReAct (2022)', 'https://arxiv.org/abs/2210.03629'],
					['Claude', 'Building agents with the Claude Agent SDK', 'https://claude.com/blog/building-agents-with-the-claude-agent-sdk'],
					['Model Context Protocol', 'What is MCP?', 'https://modelcontextprotocol.io/docs/getting-started/intro'],
					['Agent Skills', 'The open format for skills', 'https://agentskills.io/'],
					['Claude Code', 'Hooks reference', 'https://code.claude.com/docs/en/hooks'],
					['MotherDuck', 'White-label MCP server', 'https://motherduck.com/docs/key-tasks/ai-and-motherduck/mcp-workflows/white-label-mcp-server/'],
				].map(([who, what, url]) => (
					<a key={url} href={url} target="_blank" rel="noopener noreferrer" className="flex gap-3 py-1" style={{ borderBottom: '1px solid #3838382a' }}>
						<b className="w-40" style={{ fontFamily: MONO, fontSize: 12 }}>
							{who}
						</b>
						<span>{what} ↗</span>
					</a>
				))}
			</div>
		),
	},
	{
		id: 'thanks',
		section: 'THANK YOU',
		title: '',
		notes: 'Leave up during Q&A.',
		render: () => (
			<div className="flex flex-col justify-center h-full">
				<h1 className="text-6xl" style={{ fontFamily: MONO }}>
					THANKS!
				</h1>
				<p className="mt-4 text-sm" style={{ fontFamily: MONO, color: C.garden }}>
					Mehdi Ouazza · Jacob Matson · MotherDuck
				</p>
			</div>
		),
	},
];

const THEMED = new Set(['l1', 'l2', 'solved']);

export default function WorkshopDeck() {
	const [index, setIndex] = useDiveState<number>('slide', 0);
	const [reveal, setReveal] = useState(false);
	const [notes, setNotes] = useState(false);
	const current = Math.min(Math.max(0, N(index)), SLIDES.length - 1);
	const slide = SLIDES[current];
	const move = (to: number) => {
		setReveal(false);
		setIndex(Math.min(Math.max(0, to), SLIDES.length - 1));
	};
	const go = (id: string) => move(SLIDES.findIndex((s) => s.id === id));

	useEffect(() => {
		const key = (e: KeyboardEvent) => {
			if (e.key === 'ArrowRight' || e.key === ' ') move(current + 1);
			else if (e.key === 'ArrowLeft') move(current - 1);
			else if (e.key.toLowerCase() === 'r') setReveal((v) => !v);
			else if (e.key.toLowerCase() === 'n') setNotes((v) => !v);
		};
		window.addEventListener('keydown', key);
		return () => window.removeEventListener('keydown', key);
	}, [current]);

	const dark = THEMED.has(slide.id);
	const btn = {
		border: `1px solid ${C.ink}`,
		background: C.white,
		fontFamily: MONO,
		cursor: 'pointer',
	} as CSSProperties;

	return (
		<main className="p-6 flex flex-col" style={{ background: dark ? C.duck : C.sand, color: C.ink, minHeight: 600 }}>
			<div className="flex items-center justify-between">
				<span className="text-xs uppercase" style={{ fontFamily: MONO, letterSpacing: 2 }}>
					{slide.section}
				</span>
				<div className="flex gap-2 text-xs">
					<button style={btn} className="px-2 py-1" onClick={() => setReveal((v) => !v)}>
						{reveal ? 'HIDE · R' : 'REVEAL · R'}
					</button>
					<button style={btn} className="px-2 py-1" onClick={() => setNotes((v) => !v)}>
						NOTES · N
					</button>
				</div>
			</div>
			{slide.title && (
				<h2 className="text-3xl mt-2 mb-6 uppercase" style={{ fontFamily: MONO, letterSpacing: -0.5 }}>
					{slide.title}
				</h2>
			)}
			<section className="flex-1" style={{ minHeight: 360 }}>
				{slide.render({ reveal, go })}
			</section>
			{notes && (
				<aside className="mt-4 p-3 text-sm" style={box('#fffbe0')}>
					{slide.notes}
				</aside>
			)}
			<footer className="flex items-center justify-between mt-4 text-xs" style={{ fontFamily: MONO }}>
				<button style={btn} className="px-3 py-1 flex items-center gap-1" disabled={current === 0} onClick={() => move(current - 1)}>
					<ArrowLeft size={14} /> PREV
				</button>
				<span>
					MOTHERDUCK · WORKSHOP DRAFT · {String(current + 1).padStart(2, '0')} / {SLIDES.length}
				</span>
				<button style={btn} className="px-3 py-1 flex items-center gap-1" disabled={current === SLIDES.length - 1} onClick={() => move(current + 1)}>
					NEXT <ArrowRight size={14} />
				</button>
			</footer>
			<div style={{ height: 4, background: C.duck, width: `${((current + 1) / SLIDES.length) * 100}%` }} />
		</main>
	);
}
