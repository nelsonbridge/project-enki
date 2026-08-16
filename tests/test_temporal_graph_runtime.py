from datetime import datetime, timezone
import pytest
from pydantic import ValidationError
from nks.enki.temporal_graph import TemporalGraphEdgeType, TemporalGraphLifecycleStatus, TemporalGraphNodeType, TemporalGraphPromotion, TemporalGraphRecord, TemporalGraphRecordKind, TemporalGraphStore

T0=datetime(2026,1,1,tzinfo=timezone.utc); T1=datetime(2026,2,1,tzinfo=timezone.utc); T2=datetime(2026,3,1,tzinfo=timezone.utc); T3=datetime(2026,4,1,tzinfo=timezone.utc)

def node(rid, **kw):
    d=dict(graph_record_id=rid,graph_namespace="project:enki",record_kind=TemporalGraphRecordKind.NODE,node_type=TemporalGraphNodeType.OBSERVATION,domain_id="general",context_ids=("ctx",),content={"value":rid},provenance_refs=(f"source:{rid}",),recorded_at=T0,effective_from=T0,effective_to=None,authority_from=T0,authority_to=None,superseded_at=None,lifecycle_status=TemporalGraphLifecycleStatus.ACTIVE)
    d.update(kw); return TemporalGraphRecord(**d)

def test_dual_time_retroactive_knowledge():
    r=node("retro",recorded_at=T2,effective_from=T0,authority_from=T2); s=TemporalGraphStore([r])
    assert s.query(as_of=T1,known_at=T1).known_record_ids == ()
    assert s.query(as_of=T1,known_at=T3).effective_record_ids == ("retro",)

def test_unknown_effective_time_stays_unknown():
    s=TemporalGraphStore([node("unknown",effective_from=None)]).query(as_of=T2,known_at=T2)
    assert s.effective_record_ids == (); assert s.unknown_effective_record_ids == ("unknown",)

def test_historical_authority_survives_supersession():
    old=node("old",lifecycle_status=TemporalGraphLifecycleStatus.SUPERSEDED,authority_to=T2,superseded_at=T2); new=node("new",recorded_at=T2,effective_from=T2,authority_from=T2)
    store=TemporalGraphStore([old,new]); assert store.query(as_of=T1,known_at=T3,authority_at=T1).authoritative_record_ids == ("old",); assert store.query(as_of=T3,known_at=T3,authority_at=T3).authoritative_record_ids == ("new",)

def test_candidate_cause_cannot_assert_authority():
    with pytest.raises(ValidationError,match="candidate_cause_of"):
        TemporalGraphRecord(graph_record_id="e",graph_namespace="project:enki",record_kind=TemporalGraphRecordKind.EDGE,edge_type=TemporalGraphEdgeType.CANDIDATE_CAUSE_OF,domain_id="general",source_record_id="a",target_record_id="b",provenance_refs=("source:e",),recorded_at=T0,effective_from=T0,effective_to=None,authority_from=T0,authority_to=None,superseded_at=None,lifecycle_status=TemporalGraphLifecycleStatus.ACTIVE)

def test_cross_namespace_promotion_is_governed():
    p=TemporalGraphPromotion(source_namespace="project:golden-nibiru",target_namespace="project:enki",reconciliation_ref="r",authority_decision_ref="a")
    assert node("p",promotion=p).promotion == p
    with pytest.raises(ValidationError,match="target namespace"): node("bad",graph_namespace="project:other",promotion=p)

def test_hashes_are_order_independent():
    a=node("a"); b=node("b",recorded_at=T1); x=TemporalGraphStore([a,b]); y=TemporalGraphStore([b,a]); assert x.store_hash == y.store_hash; assert x.query(as_of=T2,known_at=T2).snapshot_hash == y.query(as_of=T2,known_at=T2).snapshot_hash
