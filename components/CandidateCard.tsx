'use client';

import React from 'react';
import { CandidateProfile } from '../types';
import { Mail, Phone, MapPin, Briefcase, GraduationCap, Link2, ExternalLink } from 'lucide-react';

interface CandidateCardProps {
  profile: CandidateProfile;
}

export default function CandidateCard({ profile }: CandidateCardProps) {
  // Helper to format squashed parsed strings (e.g. "School|City" -> "School | City")
  const formatParsedText = (text?: string) => {
    if (!text) return '';
    return text
      .replace(/,(?!\s)/g, ', ') // Insert space after comma if missing
      .replace(/\|/g, ' | ')      // Add space around pipe separators
      .replace(/\s+/g, ' ')      // Remove multiple spaces
      .trim();
  };

  // Helper to keep skill pills clean and prevent sentence overflow
  const formatSkill = (name: string) => {
    if (name.length > 28) {
      return name.substring(0, 25) + '...';
    }
    return name;
  };

  const getConfidenceStyle = (score: number) => {
    if (score >= 0.9) return 'text-emerald-700 bg-emerald-50 dark:bg-emerald-950/20 border-emerald-250 dark:border-emerald-900/30';
    if (score >= 0.75) return 'text-amber-700 bg-amber-50 dark:bg-amber-950/20 border-amber-250 dark:border-amber-900/30';
    return 'text-red-700 bg-red-50 dark:bg-red-950/20 border-red-250 dark:border-red-900/30';
  };

  return (
    <div className="bg-card text-card-foreground rounded-2xl border border-border/80 shadow-md p-6 sm:p-8 space-y-7 transition-all duration-200">
      
      {/* 1. Profile Header section */}
      <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
        <div className="space-y-2">
          <h2 className="text-2xl font-bold tracking-tight text-foreground">
            {profile.full_name || 'Unnamed Candidate'}
          </h2>
          {profile.headline && (
            <p className="text-sm font-medium text-muted-foreground leading-relaxed">
              {formatParsedText(profile.headline)}
            </p>
          )}
          
          <div className="flex flex-wrap items-center gap-x-4 gap-y-1.5 pt-1 text-xs text-muted-foreground">
            {profile.location.country && (
              <span className="flex items-center gap-1.5">
                <MapPin className="h-3.5 w-3.5 text-indigo-500/70" />
                <span>
                  {formatParsedText([profile.location.city, profile.location.region, profile.location.country].filter(Boolean).join(', '))}
                </span>
              </span>
            )}
            
            {profile.years_experience !== undefined && (
              <span className="flex items-center gap-1.5">
                <Briefcase className="h-3.5 w-3.5 text-indigo-500/70" />
                <span>{profile.years_experience} Years of Experience</span>
              </span>
            )}
          </div>
        </div>

        {/* Dynamic overall confidence badge */}
        <div className={`inline-flex items-center rounded-full border px-3.5 py-1 text-xs font-bold shrink-0 shadow-sm ${getConfidenceStyle(profile.overall_confidence)}`}>
          {(profile.overall_confidence * 100).toFixed(0)}% Overall Confidence
        </div>
      </div>

      {/* 2. Contact Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 py-4 px-5 rounded-xl bg-muted/40 border border-border/40 text-xs font-medium text-muted-foreground">
        <div className="space-y-2.5">
          <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400 dark:text-slate-500">Emails</p>
          {profile.emails.map((email) => (
            <div key={email} className="flex items-center gap-2 text-foreground/80 hover:text-indigo-500 transition-colors">
              <Mail className="h-3.5 w-3.5 shrink-0 opacity-60" />
              <span className="truncate select-all">{email}</span>
            </div>
          ))}
          {profile.emails.length === 0 && (
            <div className="text-slate-450 italic">No email address parsed</div>
          )}
        </div>

        <div className="space-y-2.5">
          <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400 dark:text-slate-500">Phones</p>
          {profile.phones.map((phone) => (
            <div key={phone} className="flex items-center gap-2 text-foreground/80 hover:text-indigo-500 transition-colors">
              <Phone className="h-3.5 w-3.5 shrink-0 opacity-60" />
              <span className="select-all">{phone}</span>
            </div>
          ))}
          {profile.phones.length === 0 && (
            <div className="text-slate-450 italic">No phone parsed</div>
          )}
        </div>
      </div>

      {/* 3. Work Experience */}
      {profile.experience && profile.experience.length > 0 && (
        <div className="space-y-4 pt-2">
          <h3 className="text-xs font-bold text-slate-400 dark:text-slate-500 uppercase tracking-wider">
            Work Experience
          </h3>
          <div className="space-y-5">
            {profile.experience.map((exp, idx) => (
              <div key={idx} className="flex gap-4 group">
                <div className="flex flex-col items-center shrink-0">
                  <div className="h-2.5 w-2.5 rounded-full bg-indigo-550 border border-white dark:border-slate-950 mt-1.5 shadow-sm group-hover:scale-125 transition-transform" />
                  {idx < profile.experience.length - 1 && (
                    <div className="w-0.5 flex-1 bg-border/60 dark:bg-border/30 mt-2" />
                  )}
                </div>
                <div className="space-y-1 pb-1">
                  <h4 className="text-sm font-semibold text-foreground">
                    {exp.title}
                  </h4>
                  <p className="text-xs font-medium text-indigo-650 dark:text-indigo-400">
                    {formatParsedText(exp.company)} • {exp.start || 'Unknown'} - {exp.end || 'Present'}
                  </p>
                  {exp.summary && (
                    <p className="text-xs text-muted-foreground mt-1.5 leading-relaxed break-words max-w-2xl">
                      {formatParsedText(exp.summary)}
                    </p>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 4. Education section */}
      {profile.education && profile.education.length > 0 && (
        <div className="space-y-4 pt-2">
          <h3 className="text-xs font-bold text-slate-400 dark:text-slate-500 uppercase tracking-wider">
            Education History
          </h3>
          <div className="grid grid-cols-1 gap-4">
            {profile.education.map((edu, idx) => (
              <div 
                key={idx} 
                className="flex items-start gap-4 p-4 rounded-xl bg-muted/20 border border-border/50 hover:bg-muted/30 hover:border-border transition-all duration-200"
              >
                <div className="p-2.5 rounded-lg bg-indigo-50 dark:bg-indigo-950/30 text-indigo-600 dark:text-indigo-455 border border-indigo-100/40 dark:border-indigo-900/30 mt-0.5 shrink-0 shadow-sm">
                  <GraduationCap className="h-4.5 w-4.5" />
                </div>
                <div className="space-y-1 min-w-0">
                  <h4 className="text-sm font-bold text-foreground leading-normal break-words">
                    {formatParsedText(edu.institution || 'Unknown Institution')}
                  </h4>
                  <p className="text-xs text-muted-foreground leading-relaxed break-words">
                    {formatParsedText(edu.degree || 'Degree')} {edu.field ? `in ${formatParsedText(edu.field)}` : ''}
                  </p>
                  {edu.end_year && (
                    <span className="inline-block mt-1 bg-slate-100 dark:bg-slate-900 text-slate-600 dark:text-slate-400 px-2 py-0.5 rounded text-[10px] font-bold">
                      Graduation Year: {edu.end_year}
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 5. Skills Tags */}
      {profile.skills && profile.skills.length > 0 && (
        <div className="space-y-3 pt-2">
          <h3 className="text-xs font-bold text-slate-400 dark:text-slate-500 uppercase tracking-wider">
            Canonical Skills
          </h3>
          <div className="flex flex-wrap gap-2">
            {profile.skills.map((skill, index) => {
              const score = skill.confidence;
              let skillColor = 'bg-muted text-foreground/80 border-border hover:bg-muted/70';
              if (score >= 0.9) {
                skillColor = 'bg-emerald-50 text-emerald-800 border-emerald-200/50 hover:bg-emerald-100/50 dark:bg-emerald-950/20 dark:text-emerald-400 dark:border-emerald-900/30';
              } else if (score >= 0.75) {
                skillColor = 'bg-amber-50 text-amber-800 border-amber-200/50 hover:bg-amber-100/50 dark:bg-amber-950/20 dark:text-amber-400 dark:border-amber-900/30';
              }

              return (
                <span 
                  key={index} 
                  className={`inline-flex items-center gap-1.5 rounded-lg border px-2.5 py-1 text-xs font-semibold shadow-sm transition-colors duration-150 ${skillColor}`}
                  title={`${skill.name} (Confidence: ${(score * 100).toFixed(0)}%)`}
                >
                  <span className="truncate max-w-[160px]">{formatSkill(skill.name)}</span>
                  <span className="text-[9px] opacity-75 font-mono">{(score * 100).toFixed(0)}%</span>
                </span>
              );
            })}
          </div>
        </div>
      )}

      {/* 6. Links */}
      {(profile.links.linkedin || profile.links.github || profile.links.portfolio || (profile.links.other && profile.links.other.length > 0)) && (
        <div className="space-y-3 pt-2">
          <h3 className="text-xs font-bold text-slate-400 dark:text-slate-500 uppercase tracking-wider">
            Web Presence
          </h3>
          <div className="flex flex-wrap gap-4 text-xs font-semibold">
            {profile.links.linkedin && (
              <a 
                href={profile.links.linkedin} 
                target="_blank" 
                rel="noreferrer" 
                className="flex items-center gap-1.5 text-muted-foreground hover:text-indigo-650 dark:hover:text-indigo-400 transition-colors"
              >
                <Link2 className="h-4 w-4" />
                <span>LinkedIn</span>
                <ExternalLink className="h-3 w-3 opacity-60" />
              </a>
            )}
            
            {profile.links.github && (
              <a 
                href={profile.links.github} 
                target="_blank" 
                rel="noreferrer" 
                className="flex items-center gap-1.5 text-muted-foreground hover:text-indigo-650 dark:hover:text-indigo-400 transition-colors"
              >
                <Link2 className="h-4 w-4" />
                <span>GitHub</span>
                <ExternalLink className="h-3 w-3 opacity-60" />
              </a>
            )}

            {profile.links.portfolio && (
              <a 
                href={profile.links.portfolio} 
                target="_blank" 
                rel="noreferrer" 
                className="flex items-center gap-1.5 text-muted-foreground hover:text-indigo-650 dark:hover:text-indigo-400 transition-colors"
              >
                <Link2 className="h-4 w-4" />
                <span>Portfolio</span>
                <ExternalLink className="h-3 w-3 opacity-60" />
              </a>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
