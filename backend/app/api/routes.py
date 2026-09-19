"""
FastAPI REST API Routes for SwarmIQ.
Endpoints for mission control, status inspection, preset scenarios, and manual fault injection.
"""

from fastapi import APIRouter, HTTPException, Path, Body
from typing import Dict, Any

from app.core.simulation_loop import engine
from app.models.schemas import (
    MissionCreateRequest,
    FormationChangeRequest,
    MissionState,
    SimulationMetrics,
    SimulationSnapshot,
    FormationType,
)

router = APIRouter(prefix="/api")


@router.get("/health")
async def health_check() -> Dict[str, str]:
    return {"status": "ok", "app": "SwarmIQ Drone Simulator", "version": "1.0.0"}


@router.post("/mission/create")
async def create_mission(req: MissionCreateRequest) -> Dict[str, Any]:
    target_pos = req.target.to_list() if req.target else None
    start_pos = req.start_position.to_list() if req.start_position else None

    engine.reset(
        drone_count=req.drone_count,
        start_pos=start_pos,
        target_pos=target_pos,
        formation=req.formation,
    )
    return {"status": "created", "mission": engine.mission.to_state()}


@router.post("/mission/start")
async def start_mission() -> Dict[str, str]:
    engine.start()
    return {"status": "started"}


@router.post("/mission/pause")
async def pause_mission() -> Dict[str, str]:
    engine.pause()
    return {"status": "paused"}


@router.post("/mission/resume")
async def resume_mission() -> Dict[str, str]:
    engine.resume()
    return {"status": "resumed"}


@router.post("/mission/reset")
async def reset_mission() -> Dict[str, str]:
    engine.reset()
    return {"status": "reset"}


@router.get("/mission/status")
async def get_mission_status() -> Dict[str, Any]:
    return {
        "mission": engine.mission.to_state(),
        "leader_id": engine.swarm.leader_id,
    }


@router.get("/metrics")
async def get_simulation_metrics() -> SimulationMetrics:
    return engine.swarm.get_metrics(
        fps=engine.measured_rate,
        update_rate=engine.measured_rate,
    )


@router.post("/mission/scenario/{scenario_id}")
async def load_scenario(
    scenario_id: int = Path(..., ge=1, le=5, description="Scenario ID (1 to 5)")
) -> Dict[str, Any]:
    engine.load_scenario(scenario_id)
    return {
        "status": "loaded",
        "scenario_id": scenario_id,
        "drone_count": len(engine.swarm.drones),
        "formation": engine.mission.formation,
        "obstacle_count": len(engine.environment.obstacles),
    }


@router.post("/config/formation")
async def update_formation(req: FormationChangeRequest) -> Dict[str, str]:
    engine.set_formation(req.formation)
    return {"status": "updated", "formation": req.formation}


@router.post("/drone/{drone_id}/fail")
async def trigger_drone_failure(drone_id: str) -> Dict[str, Any]:
    if drone_id not in engine.swarm.drones:
        raise HTTPException(status_code=404, detail=f"Drone {drone_id} not found")

    drone = engine.swarm.drones[drone_id]
    was_leader = (drone.id == engine.swarm.leader_id)
    drone.fail()

    if was_leader:
        new_id, _ = engine.leader_election.elect_leader(
            list(engine.swarm.drones.values()),
            engine.mission.target_position,
            engine.swarm.leader_id,
        )
        if new_id:
            engine.swarm.set_leader(new_id)
            engine.replan_needed = True

    return {
        "status": "failed",
        "drone_id": drone_id,
        "was_leader": was_leader,
        "new_leader_id": engine.swarm.leader_id,
    }
