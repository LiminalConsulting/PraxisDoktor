<script lang="ts">
	import {
		UserPlus, Receipt, MessageSquare, Calendar, ClipboardList, FileText,
		Package, Users, Mail, Square, MessageCircleHeart, FolderOpen, Lightbulb
	} from 'lucide-svelte';

	let { name, size = 20 }: { name: string; size?: number } = $props();

	const map: Record<string, any> = {
		'user-plus': UserPlus,
		receipt: Receipt,
		'message-square': MessageSquare,
		calendar: Calendar,
		'clipboard-list': ClipboardList,
		'file-text': FileText,
		'folder-open': FolderOpen,
		package: Package,
		users: Users,
		mail: Mail,
		lightbulb: Lightbulb,
		'message-circle-heart': MessageCircleHeart,
		square: Square
	};
	const Icon = $derived(map[name] || Square);
</script>

<Icon {size} />
