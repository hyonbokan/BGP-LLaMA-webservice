import { useState } from 'react';
import { MessageSquarePlus, MoreVertical, Pencil, Trash2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { cn } from '@/lib/utils';
import type { ChatTab } from '@/types';

export function ChatSidebar({
  tabs,
  currentTab,
  onSelect,
  onNewChat,
  onRename,
  onDelete,
}: {
  tabs: ChatTab[];
  currentTab: number;
  onSelect: (index: number) => void;
  onNewChat: () => void;
  onRename: (id: number, label: string) => void;
  onDelete: (id: number) => void;
}) {
  const [renaming, setRenaming] = useState<ChatTab | null>(null);
  const [renameValue, setRenameValue] = useState('');

  const openRename = (tab: ChatTab) => {
    setRenaming(tab);
    setRenameValue(tab.label);
  };

  const saveRename = () => {
    if (renaming && renameValue.trim()) onRename(renaming.id, renameValue.trim());
    setRenaming(null);
  };

  return (
    <>
      <div className="flex h-full w-64 flex-col border-r border-border bg-card/40">
        <div className="p-3">
          <Button className="w-full justify-start gap-2 font-mono" onClick={onNewChat}>
            <MessageSquarePlus className="h-4 w-4" /> New chat
          </Button>
        </div>
        <nav className="flex-1 space-y-1 overflow-y-auto px-2 pb-3">
          {tabs.map((tab, index) => (
            <div
              key={tab.id}
              className={cn(
                'group flex items-center gap-1 rounded-md pr-1 transition-colors',
                index === currentTab ? 'bg-accent' : 'hover:bg-accent/60'
              )}
            >
              <button
                onClick={() => onSelect(index)}
                className="flex-1 truncate px-2 py-2 text-left text-sm"
              >
                {tab.label}
              </button>
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-7 w-7 opacity-0 group-hover:opacity-100 data-[state=open]:opacity-100"
                    aria-label="Chat options"
                  >
                    <MoreVertical className="h-4 w-4" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end">
                  <DropdownMenuItem onClick={() => openRename(tab)}>
                    <Pencil /> Rename
                  </DropdownMenuItem>
                  <DropdownMenuItem
                    disabled={tabs.length === 1}
                    className="text-destructive focus:text-destructive"
                    onClick={() => onDelete(tab.id)}
                  >
                    <Trash2 /> Delete
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </div>
          ))}
        </nav>
      </div>

      <Dialog open={renaming !== null} onOpenChange={(o) => !o && setRenaming(null)}>
        <DialogContent className="max-w-sm">
          <DialogHeader>
            <DialogTitle>Rename chat</DialogTitle>
            <DialogDescription>Give this conversation a new name.</DialogDescription>
          </DialogHeader>
          <div className="space-y-2">
            <Label htmlFor="chat-name">Chat name</Label>
            <Input
              id="chat-name"
              autoFocus
              value={renameValue}
              onChange={(e) => setRenameValue(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && saveRename()}
            />
          </div>
          <DialogFooter>
            <Button variant="ghost" onClick={() => setRenaming(null)}>
              Cancel
            </Button>
            <Button onClick={saveRename}>Save</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
