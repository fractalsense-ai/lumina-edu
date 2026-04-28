/**
 * Education domain-pack UI plugin.
 *
 * Registers:
 *  - Vocabulary complexity chat hook (passive, client-side analysis)
 *  - Education-scoped student assignment request command
 */

import type { DomainPlugin, PluginRegistration, SlashCommandDef } from '@lumina/plugins'
import { analyzeVocabulary, postVocabularyMetric } from './services/vocabularyAnalyzer'

// ── Education slash commands ───────────────────────────────

const EDUCATION_COMMANDS: SlashCommandDef[] = [
  {
    name: 'join',
    operation: 'request_teacher_assignment',
    description: 'Request assignment to a teacher or teaching assistant',
    args: ['teacher_id'],
    allowedRoles: ['student'],
    domainScope: 'education',
    tier: 'user',
  },
]

// ── Vocabulary analysis chat hook ──────────────────────────

/** State tracker to avoid re-analyzing the same session. */
let vocabAnalyzed = false

function resetVocabState() {
  vocabAnalyzed = false
}

// ── Plugin definition ──────────────────────────────────────

const educationPlugin: DomainPlugin = {
  id: 'education',

  register(api: PluginRegistration) {
    api.addSlashCommands(EDUCATION_COMMANDS)

    api.addChatHooks([
      {
        id: 'education:vocab-analysis',
        async onMessagesChanged(ctx) {
          if (vocabAnalyzed) return
          const studentMsgs = ctx.messages
            .filter((m) => m.role === 'user')
            .map((m) => m.content)
          if (studentMsgs.length < 10) return
          vocabAnalyzed = true
          const metric = await analyzeVocabulary(studentMsgs)
          if (metric) {
            await postVocabularyMetric(
              ctx.apiBase,
              ctx.auth.token,
              ctx.auth.userId,
              metric,
            )
          }
        },
      },
    ])
  },
}

export default educationPlugin
export { resetVocabState }
