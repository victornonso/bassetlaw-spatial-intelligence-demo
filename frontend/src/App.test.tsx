import {describe,it,expect} from 'vitest';
import {render,screen} from '@testing-library/react';
import {LocationInsight} from './main';
import {featureName,featureId,type Insight} from './api';
describe('Location evidence record',()=>{
 it('does not interpret missing flood data as no risk',()=>{const i:Insight={location:{lat:53.3,lon:-1},area:{district:'Bassetlaw',ward:'Example'},evidence:{flood:{status:'unavailable',summary:'No data loaded for this indicator.'}},sources:[],method:{mode:'snapshot',distance:'Straight-line'}};render(<LocationInsight insight={i} loading={false} error=""/>);expect(screen.getAllByText('Evidence temporarily unavailable. Please retry.').length).toBeGreaterThan(0);expect(screen.queryByText('No risk')).toBeNull();expect(screen.getByText('53.30000° N, 1.00000° W')).toBeInTheDocument();});
 it('displays a recoverable error',()=>{render(<LocationInsight insight={null} loading={false} error="Try again."/>);expect(screen.getByRole('alert')).toHaveTextContent('Location evidence is temporarily unavailable.');});
 it('identifies a real geography name and code schema',()=>{const f={type:'Feature' as const,geometry:{type:'Point' as const,coordinates:[0,0]},properties:{WD24NM:'Worksop',WD24CD:'E05000000'}};expect(featureName(f)).toBe('Worksop');expect(featureId(f)).toBe('E05000000');});
});
