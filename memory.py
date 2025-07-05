from couchbase.cluster import Cluster
from couchbase.options import ClusterOptions
from couchbase.auth import PasswordAuthenticator
from couchbase.exceptions import DocumentNotFoundException


class CouchbaseMemory:
    def __init__(
        self,
        conn_str: str,
        username: str,
        password: str,
        bucket_name: str,
        scope_name: str = "real_estate",
        collection_name: str = "memory",
    ):
        """
        Initialize Couchbase memory system.
        
        Args:
            conn_str (str): Connection string to Couchbase
            username (str): Username for authentication
            password (str): Password for authentication
            bucket_name (str): Name of the bucket to use
            scope_name (str): Scope name for the memory system
            collection_name (str): Collection name for the memory system
        """
        self.cluster = Cluster(
            conn_str, ClusterOptions(PasswordAuthenticator(username, password))
        )
        self.bucket = self.cluster.bucket(bucket_name)
        self.scope = self.bucket.scope(scope_name)
        self.collection = self.scope.collection(collection_name)
        print("[Memory System] Connected to Couchbase Capella")

    def _doc_id(self, user_id: str) -> str:
        """Generate document ID for a user."""
        return f"user::{user_id}"

    def add(self, user_id: str, category: str, data: str) -> bool:
        """
        Add data to a user's memory in a specific category.
        
        Args:
            user_id (str): User ID to associate the data with
            category (str): Category to store the data in
            data (str): Data to store
            
        Returns:
            bool: True if successful
        """
        doc_id = self._doc_id(user_id)
        try:
            doc = self.collection.get(doc_id).content_as[dict]
        except DocumentNotFoundException:
            doc = {}

        doc.setdefault(category, [])
        if data not in doc[category]:
            doc[category].append(data)
            self.collection.upsert(doc_id, doc)
            print(
                f"[Memory System] Saved data for user '{user_id}' in category '{category}': '{data}'"
            )
        return True

    def search_by_category(self, user_id: str, category: str) -> list:
        """
        Search for data in a specific category for a user.
        
        Args:
            user_id (str): User ID to search for
            category (str): Category to search in
            
        Returns:
            list: List of items found in the category
        """
        doc_id = self._doc_id(user_id)
        try:
            doc = self.collection.get(doc_id).content_as[dict]
            results = doc.get(category, [])
        except DocumentNotFoundException:
            results = []
        print(
            f"[Memory System] Retrieved {len(results)} items from category '{category}' for user '{user_id}'."
        )
        return results
