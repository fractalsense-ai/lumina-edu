/**
 * Education Commons domain-pack UI plugin.
 *
 * Registers student support and Guardian relationship commands.
 */

import type { DomainPlugin, PluginRegistration, SlashCommandDef } from '@lumina/plugins'

const EDUCATION_COMMONS_COMMANDS: SlashCommandDef[] = [
  {
    name: 'guardian',
    operation: 'assign_guardian',
    description: 'Assign a guardian for yourself or a student',
    args: ['guardian_id', 'student_id'],
    allowedRoles: ['student', 'guardian'],
    domainScope: 'education-commons',
    tier: 'user',
  },
  {
    name: 'assign',
    operation: 'assign_guardian',
    description: 'Assign a guardian for yourself or a student - use /assign guardian <guardian_id> [student_id]',
    args: ['guardian_id', 'student_id'],
    allowedRoles: ['student', 'guardian'],
    domainScope: 'education-commons',
    tier: 'user',
    subCommands: {
      guardian: {
        operation: 'assign_guardian',
        args: ['guardian_id', 'student_id'],
      },
    },
  },
]

const educationCommonsPlugin: DomainPlugin = {
  id: 'education-commons',

  register(api: PluginRegistration) {
    api.addSlashCommands(EDUCATION_COMMONS_COMMANDS)
  },
}

export default educationCommonsPlugin
