import json
from collections import defaultdict

import numpy as np
from sklearn.cluster import DBSCAN

from infra.exceptions import AgentException
from providers.factory import ProviderFactory


class FailureClusterAnalyzer:
    def cluster(self, embeddings: list[list[float]]) -> list[int]:
        X = np.array(embeddings)
        labels = DBSCAN(eps=0.5, min_samples=2).fit_predict(X)
        return labels.tolist()

    async def get_embeddings(
        self, texts: list[str], model: str
    ) -> list[list[float]]:
        provider = ProviderFactory.get_provider(model)
        results = []
        for text in texts:
            output = await provider.complete(
                system_message="Return a JSON array of floats representing the embedding vector for the input text.",
                user_message=text,
            )
            try:
                vector = json.loads(output.text)
            except (json.JSONDecodeError, ValueError):
                raise AgentException(
                    message="Failed to parse embedding from provider output",
                    context={"raw_output": output.text},
                )
            results.append([float(v) for v in vector])
        return results

    async def label_cluster(
        self, texts: list[str], model: str
    ) -> str:
        sample = texts[:5]
        joined = "\n".join(f"- {t}" for t in sample)
        provider = ProviderFactory.get_provider(model)
        output = await provider.complete(
            system_message="You are analyzing failure patterns. Given a sample of evaluation justifications from a single failure cluster, respond with a short descriptive label (max 10 words) that summarizes the common failure pattern.",
            user_message=joined,
        )
        return output.text.strip()

    async def get_failed_justifications(self) -> list[dict]:
        from db.repositories.evaluation_repository import EvaluationRepository

        return await EvaluationRepository().list_failed()

    async def analyze(
        self, evaluations: list[dict], model: str = "claude-sonnet-4-20250514"
    ) -> list[dict]:
        if not evaluations:
            return []

        texts = [
            f"{e.get('accuracy_justification', '')} {e.get('reasoning_justification', '')}"
            for e in evaluations
        ]

        embeddings = await self.get_embeddings(texts, model)
        labels = self.cluster(embeddings)

        clusters: dict[int, list[int]] = defaultdict(list)
        for idx, label in enumerate(labels):
            if label == -1:
                continue
            clusters[label].append(idx)

        result = []
        for cluster_id, indices in clusters.items():
            cluster_texts = [texts[i] for i in indices]
            label = await self.label_cluster(cluster_texts, model)
            result.append(
                {
                    "cluster_id": cluster_id,
                    "label": label,
                    "size": len(indices),
                    "evaluation_ids": [evaluations[i]["public_id"] for i in indices],
                }
            )

        return result
