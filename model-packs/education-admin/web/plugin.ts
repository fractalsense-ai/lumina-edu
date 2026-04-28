/**
 * Education Admin domain-pack UI plugin.
 *
 * Registers staff/governance slash commands and administrative roster views.
 */

import type { DomainPlugin, DashboardTabDef, SidebarPanelDef, SlashCommandDef, PanelComponentProps } from '@lumina/plugins'
import type { ComponentType } from 'react'
import { createElement } from 'react'
import { ClassroomPanel } from './components/ClassroomPanel'
import { TeacherOverview } from './components/TeacherOverview'

type LegacyProps = { auth: { token: string; userId: string; username: string; role: string }; domainId?: string; domainKey?: string }

function wrapLegacy(
  Comp: ComponentType<LegacyProps>,
): ComponentType<PanelComponentProps> {
  return function LegacyWrapper({ auth, domainId, domainKey }: PanelComponentProps) {
    return createElement(Comp, { auth, domainId, domainKey })
  }
}

const EDUCATION_ADMIN_COMMANDS: SlashCommandDef[] = [
  {
    name: 'teachers',
    operation: 'list_users',
    description: 'Show available teachers',
    args: [],
    defaultParams: { domain_role: 'teacher', domain_id: 'education-admin' },
    allowedRoles: ['teaching_assistant', 'teacher', 'domain_authority'],
    domainScope: 'education-admin',
    aliases: ['list_teachers'],
    tier: 'user',
  },
  {
    name: 'students',
    operation: 'list_users',
    description: 'List your students',
    args: [],
    defaultParams: { domain_role: 'student', domain_id: 'education-admin' },
    allowedRoles: ['teaching_assistant', 'teacher', 'domain_authority'],
    domainScope: 'education-admin',
    tier: 'user',
  },
  {
    name: 'assign',
    operation: 'assign_student',
    description: 'Assign a student, TA, or learning module - use /assign ta|module|modules <args>',
    args: ['student_id'],
    allowedRoles: ['teacher', 'domain_authority'],
    domainScope: 'education-admin',
    tier: 'user',
    subCommands: {
      module: {
        operation: 'assign_module',
        args: ['user_id', 'module_id'],
      },
      modules: {
        operation: 'assign_modules',
        args: ['target', 'module_ids'],
        joinTrailingArgs: true,
      },
      ta: {
        operation: 'assign_ta',
        args: ['ta_id', 'student_ids'],
        joinTrailingArgs: true,
      },
    },
  },
  {
    name: 'assignmodules',
    operation: 'assign_modules',
    description: 'Assign learning modules to a student, classroom, or self',
    args: ['module_ids', 'target'],
    allowedRoles: ['teacher', 'domain_authority'],
    domainScope: 'education-admin',
    tier: 'user',
  },
  {
    name: 'escalations',
    operation: 'list_escalations',
    description: 'List pending escalations',
    args: [],
    defaultParams: { domain_id: 'education-admin' },
    allowedRoles: ['teacher', 'domain_authority'],
    aliases: ['list_escalations'],
    domainScope: 'education-admin',
    tier: 'user',
  },
]

const EDUCATION_ADMIN_SIDEBAR_PANELS: SidebarPanelDef[] = [
  { name: 'ClassroomPanel', component: wrapLegacy(ClassroomPanel) },
]

const EDUCATION_ADMIN_DASHBOARD_TABS: DashboardTabDef[] = [
  {
    id: 'teacher-overview',
    label: 'Teachers',
    roles: ['root', 'admin'],
    component: TeacherOverview,
    order: 110,
  },
]

const educationAdminPlugin: DomainPlugin = {
  id: 'education-admin',
  register(api) {
    api.addSlashCommands(EDUCATION_ADMIN_COMMANDS)
    api.addDashboardTabs(EDUCATION_ADMIN_DASHBOARD_TABS)
    api.addSidebarPanels(EDUCATION_ADMIN_SIDEBAR_PANELS)
    api.addRoleEquivalences({
      teacher: 'teacher',
      teaching_assistant: 'teaching_assistant',
    })
  },
}

export default educationAdminPlugin