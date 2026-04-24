<script lang="ts">
	/**
	 * Honest gap indicator. Renders a yellow strip in a tool header when the
	 * underlying data is mocked, schema-pending, or otherwise not yet wired
	 * to the real practice data.
	 *
	 * Single source of truth: the component never lies about coverage. If a
	 * tool depends on data that's not grounded yet, this banner says exactly
	 * what's missing and what closes the gap.
	 */
	import { AlertTriangle } from 'lucide-svelte';

	type Gap = {
		title: string;
		detail: string;
		closes_with?: string;
	};

	let { gaps = [], compact = false }: { gaps: Gap[]; compact?: boolean } = $props();
</script>

{#if gaps.length > 0}
	<div class="bg-amber-50 border-b border-amber-300 px-4 py-3 flex items-start gap-3 text-sm">
		<AlertTriangle size={18} class="text-amber-700 mt-0.5 shrink-0" />
		<div class="flex-1 min-w-0">
			{#if compact}
				<div class="text-amber-900">
					<span class="font-semibold">Gap:</span>
					{gaps.map((g) => g.title).join(' · ')}
				</div>
			{:else}
				<div class="font-semibold text-amber-900 mb-1">
					{gaps.length === 1 ? 'Offene Lücke' : `${gaps.length} offene Lücken`} —
					noch nicht produktionsreif
				</div>
				<ul class="space-y-1 text-amber-900/90">
					{#each gaps as gap}
						<li>
							<span class="font-medium">{gap.title}:</span>
							{gap.detail}
							{#if gap.closes_with}
								<span class="text-amber-700/80">
									(geschlossen durch: {gap.closes_with})
								</span>
							{/if}
						</li>
					{/each}
				</ul>
			{/if}
		</div>
	</div>
{/if}
