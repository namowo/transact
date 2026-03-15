from typing import (
    Any,
    Dict,
    List,
    Literal,
    Generic,
    Optional,
    Type,
    TypeVar,
    Tuple,
    Union,
)
from collections import defaultdict

from fastapi import HTTPException, status

from sqlalchemy import asc, desc, func, or_
from sqlalchemy.engine import Result
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import aliased, joinedload, RelationshipProperty

from app.crud.exceptions import DatabaseCommitError, NotFoundError
from app.models.user import User

# Define generic type variables for models and schemas
ModelType = TypeVar("ModelType")
CreateSchemaType = TypeVar("CreateSchemaType")
UpdateSchemaType = TypeVar("UpdateSchemaType")

sorting_order = Literal["asc", "desc"]


class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: Type[ModelType]):
        """
        CRUD object with default methods to Create, Read, Update, Delete (CRUD).
        **Parameters**
        * `model`: A SQLAlchemy model class
        """
        self.model = model

    def check_user_permissions(
        self,
        user: Optional[User] = None,
        user_permissions: Optional[List[Tuple[str, Any]]] = None,
    ) -> bool:
        """
        Check if the user has the required permissions.

        Args:
            user (Optional[User]): The user object.
            user_permissions (Optional[List[Tuple[str, bool]]]): List of tuples specifying permissions required for each field.
        """
        if user is None:
            return not user_permissions  # If permissions are required, return False

        if not user_permissions:
            return True  # No specific permissions required

        return all(
            not required or getattr(user, permission, False)
            for permission, required in user_permissions
        )

    def extend_statement(
        self, statement: select, *, extra_fields: List[Any] = []
    ) -> select:
        for field in extra_fields:
            if (
                hasattr(field, "property")
                and isinstance(field.property, RelationshipProperty)
                and hasattr(self.model, field.key)
            ):
                statement = statement.options(joinedload(field))
        return statement

    def sort(
        self,
        data: Union[List[ModelType], ModelType],
        sort_params: List[
            Tuple[str, Union[str, Tuple[str, Union[str, Tuple[str, str]]]]]
        ],
    ) -> Union[List[ModelType], ModelType]:
        """
        Generalized sorting function for any object with support for deeply nested attributes.

        :param data: A single instance or a list of instances to sort.
        :param sort_params: List of tuples specifying sorting instructions:
                            - For main attributes: (field, "asc" or "desc")
                            - For nested attributes: (relationship, (field, "asc" or "desc"))
                            - Supports multi-level nesting.
        :return: The sorted data, with specified attributes sorted as per sort_params.
        """

        def sort_key(instance: Any, field: str, ascending: bool) -> Any:
            """Generate a sorting key based on a field and order."""
            value = getattr(instance, field, None)
            return (
                value
                if ascending
                else (-value if isinstance(value, (int, float)) else value)
            )

        def apply_nested_sorting(
            instance: Any, nested_sort_params: List[Tuple[str, Union[str, Tuple]]]
        ):
            """Recursively apply sorting to nested attributes."""
            for attr, sort_instruction in nested_sort_params:
                if isinstance(sort_instruction, tuple):
                    # Handle deeper nesting, e.g., "objectives.sub_objectives.no"
                    if isinstance(sort_instruction[1], tuple):
                        nested_attr, nested_sort_instruction = sort_instruction
                        nested_data = getattr(instance, attr, None)
                        if isinstance(nested_data, list):
                            # Sort the current level
                            field, order = nested_sort_instruction
                            ascending = order == "asc"
                            nested_data.sort(
                                key=lambda item: getattr(item, field),
                                reverse=not ascending,
                            )

                            # Recursively sort deeper levels
                            for item in nested_data:
                                apply_nested_sorting(
                                    item, [(nested_attr, nested_sort_instruction)]
                                )
                    else:
                        # Handle single-level nesting, e.g., "objectives.no"
                        field, order = sort_instruction
                        ascending = order == "asc"
                        nested_data = getattr(instance, attr, None)
                        if isinstance(nested_data, list):
                            nested_data.sort(
                                key=lambda item: getattr(item, field),
                                reverse=not ascending,
                            )

        # Main sorting function
        if isinstance(data, list):
            # If data is a list, apply top-level sorting
            for attr, sort_instruction in sort_params:
                if isinstance(sort_instruction, str):
                    # Top-level sorting
                    ascending = sort_instruction == "asc"
                    data.sort(key=lambda item: sort_key(item, attr, ascending))
                else:
                    # Nested attribute sorting (if it includes a tuple for deeper sorting)
                    for instance in data:
                        apply_nested_sorting(instance, [(attr, sort_instruction)])
        else:
            # If data is a single object, only apply nested sorting
            apply_nested_sorting(data, sort_params)

        return data

    async def group_by_field(
        self,
        instances: List[ModelType],  # List of SQLAlchemy model objects
        group_by: str,  # The field to group by
        fields: Optional[List[str]] = None,  # Fields to include in the nested items
    ) -> List[Dict]:
        """
        Group a list of SQLAlchemy model instances by a specified field into a nested format.

        :param instances: List of SQLAlchemy model instances.
        :param group_by: Field name to group by (e.g., 'kategorie').
        :param fields: List of fields to include in the nested items (default: all fields in the model).
        :return: List of grouped data in the specified format.
        """
        if not instances:
            return []

        # Validate that the group_by field exists in the model
        if not hasattr(instances[0], group_by):
            raise ValueError(f"Field '{group_by}' does not exist in the model.")

        # Group the records
        grouped = defaultdict(list)
        for instance in instances:
            # Get the value of the group_by field dynamically
            group_value = getattr(instance, group_by)
            if group_value:
                # Include only the specified fields in the nested items
                if fields:
                    item = {field: getattr(instance, field, None) for field in fields}
                else:
                    # Include all fields in the model if fields is not specified
                    item = {
                        column.name: getattr(instance, column.name)
                        for column in instance.__table__.columns
                    }

                grouped[group_value].append(item)

        # Transform the grouped data into the desired format
        result = [{group_by: key, "items": items} for key, items in grouped.items()]
        return result

    async def get_all(
        self,
        db: AsyncSession,
        sort_params: List[
            Tuple[str, Union[str, Tuple[str, Union[str, Tuple[str, str]]]]]
        ] = [],
        extra_fields: List[Any] = [],
    ) -> List[ModelType]:
        """
        Retrieve all records for the model, optionally filtering by municipality_id.
        """
        statement = select(self.model)
        statement = self.extend_statement(statement, extra_fields=extra_fields)

        result = await db.execute(statement)
        instances = result.scalars().all()

        if not instances:
            raise HTTPException(
                status_code=status.HTTP_204_NO_CONTENT,
                detail=f"{self.model.__name__} not found",
            )
            # raise NotFoundError(
            #     status_code=status.HTTP_204_NO_CONTENT, message=self.model.__name__
            # )

            # Apply recursive in-memory sorting for nested attributes
        instances = self.sort(instances, sort_params)

        return instances

    async def get(
        self, db: AsyncSession, id: Any, extra_fields: List[Any] = []
    ) -> Optional[ModelType]:
        """Retrieve a single record by ID."""
        statement = select(self.model).where(self.model.id == id)
        statement = self.extend_statement(statement, extra_fields=extra_fields)
        result = await db.execute(statement)
        instance = result.scalars().first()

        if instance is None:
            raise HTTPException(
                status_code=status.HTTP_204_NO_CONTENT,
                detail=f"{self.model.__name__} with ID {self.model.id} not found",
            )
            # raise NotFoundError(
            #     status_code=status.HTTP_204_NO_CONTENT,
            #     message=f"Model {self.model.__name__} with ID {self.model.id}",
            # )

        return instance

    async def get_by_key(
        self,
        db: AsyncSession,
        *,
        key: str,
        value: Any,
        only_first: bool = False,
        sort_params: List[
            Tuple[str, Union[str, Tuple[str, Union[str, Tuple[str, str]]]]]
        ] = [],
        extra_fields: List[Any] = [],
    ) -> Optional[ModelType]:
        # Check if the value is a string for case-insensitive comparison
        if isinstance(value, str):
            match value:
                case "NOTNULL":
                    statement = select(self.model).where(
                        getattr(self.model, key).isnot(None)
                    )
                case _:
                    statement = select(self.model).where(
                        func.lower(getattr(self.model, key)) == value.lower()
                    )
        else:
            statement = select(self.model).where(getattr(self.model, key) == value)

        # Extend the statement with additional fields
        statement = self.extend_statement(statement, extra_fields=extra_fields)

        # Execute the query
        result = await db.execute(statement)
        if only_first:
            instance = result.scalars().first()
            if not instance:
                raise HTTPException(
                    status_code=status.HTTP_204_NO_CONTENT,
                    detail=f"Instance of model '{self.model.__name__}' with '{key}' not found",
                )
            return instance

        instances = result.scalars().all()

        if not instances:
            raise HTTPException(
                status_code=status.HTTP_204_NO_CONTENT,
                detail=f"{self.model.__name__} with {key}={value} not found",
            )
            # raise NotFoundError(
            #     status_code=status.HTTP_204_NO_CONTENT,
            #     message=f"No {self.model.__table__.name} found with {key}={value}",
            # )

        # Apply recursive in-memory sorting for nested attributes
        instances = self.sort(instances, sort_params)

        return instances

    # async def get_by_multi_keys(
    #     self,
    #     db: AsyncSession,
    #     *,
    #     keys: Dict[str, Any],
    #     sort_params: List[
    #         Tuple[str, Union[str, Tuple[str, Union[str, Tuple[str, str]]]]]
    #     ] = [],
    #     only_first=False,
    #     extra_fields: List[Any] = [],
    # ) -> List[ModelType]:
    #     """
    #     Retrieves records matching multiple key-value pairs with optional query options,
    #     including filtering by nested relationships.

    #     Args:
    #         db (AsyncSession): The database session.
    #         keys (Dict[str, Any]): Dictionary of key-value pairs for filtering.
    #             Keys can be strings (attribute names) including nested relationships like "author.role".
    #         extra_fields (Optional[List[Any]]): Optional list of SQLAlchemy query options (e.g., joinedload).

    #     Returns:
    #         List[ModelType]: List of model instances matching the filters.
    #     """

    #     statement = select(self.model)
    #     alias_map = {}

    #     for key, value in keys.items():
    #         if value is None:
    #             continue

    #         # Split key to check for nested relationships (e.g., "author.role")
    #         nested_keys = key.split(".")
    #         if len(nested_keys) > 1:
    #             current_model = self.model
    #             for i, attr in enumerate(nested_keys):
    #                 if i < len(nested_keys) - 1:  # Intermediate relationships
    #                     # If alias doesn't exist, create it
    #                     if attr not in alias_map:
    #                         relationship_attr = getattr(current_model, attr)
    #                         alias = aliased(relationship_attr.property.mapper.class_)
    #                         alias_map[attr] = alias
    #                         statement = statement.join(alias, relationship_attr)
    #                     current_model = alias_map[attr]
    #                 else:
    #                     # Apply filter on the final attribute (e.g., "role")
    #                     statement = statement.where(
    #                         getattr(current_model, attr) == value
    #                     )
    #         else:
    #             # Simple attribute (non-nested)
    #             statement = statement.where(getattr(self.model, key) == value)

    #     # Extend statement with any extra_fields for eager loading
    #     statement = self.extend_statement(statement, extra_fields=extra_fields)

    #     result = await db.execute(statement)
    #     if only_first:
    #         instances = result.scalars().first()
    #     else:
    #         instances = result.scalars().all()

    #     if not instances:
    #         raise HTTPException(
    #             status_code=status.HTTP_204_NO_CONTENT,
    #             detail=f"Instance of model '{self.model.__name__}' with '{keys}' not found",
    #         )
    #         # raise NotFoundError(
    #         #     status_code=status.HTTP_204_NO_CONTENT,
    #         #     message=f"Instance of model '{self.model.__name__}' with '{keys}' not found",
    #         # )

    #         # Apply recursive in-memory sorting for nested attributes
    #     instances = self.sort(instances, sort_params)

    #     return instances

    async def get_by_multi_keys_(
        self,
        *,
        keys: Dict[str, Any] = {},
        extra_fields: List[Any] = [],
    ) -> str:
        statement = select(self.model)
        alias_map = {}

        for key, value in keys.items():
            if value is None:
                continue

            nested_keys = key.split(".")
            attr_name = nested_keys[-1]
            current_model = self.model

            if len(nested_keys) > 1:
                for i, attr in enumerate(nested_keys[:-1]):
                    if attr not in alias_map:
                        relationship_attr = getattr(current_model, attr)
                        alias = aliased(relationship_attr.property.mapper.class_)
                        alias_map[attr] = alias
                        statement = statement.join(alias, relationship_attr)
                    current_model = alias_map[attr]

            if attr_name.endswith("__isnot"):
                real_field = attr_name.replace("__isnot", "")
                statement = statement.where(
                    getattr(current_model, real_field).isnot(None)
                )

            elif attr_name.endswith("__isnull"):
                real_field = attr_name.replace("__isnull", "")
                statement = statement.where(
                    getattr(current_model, real_field).is_(None)
                )

            elif attr_name.endswith("__like"):
                real_field = attr_name.replace("__like", "")
                statement = statement.where(
                    getattr(current_model, real_field).like(value)
                )

            elif attr_name.endswith("__in"):
                real_field = attr_name.replace("__in", "")
                statement = statement.where(
                    getattr(current_model, real_field).in_(value)
                )

            elif attr_name.endswith("__gt"):
                real_field = attr_name.replace("__gt", "")
                statement = statement.where(getattr(current_model, real_field) > value)

            elif attr_name.endswith("__gte"):
                real_field = attr_name.replace("__gte", "")
                statement = statement.where(getattr(current_model, real_field) >= value)

            elif attr_name.endswith("__lt"):
                real_field = attr_name.replace("__lt", "")
                statement = statement.where(getattr(current_model, real_field) < value)

            elif attr_name.endswith("__lte"):
                real_field = attr_name.replace("__lte", "")
                statement = statement.where(getattr(current_model, real_field) <= value)

            else:
                statement = statement.where(getattr(current_model, attr_name) == value)

        statement = self.extend_statement(statement, extra_fields=extra_fields)

        return statement

    async def get_by_multi_keys(
        self,
        db: AsyncSession,
        *,
        keys: Dict[str, Any],
        sort_params: List[
            Tuple[str, Union[str, Tuple[str, Union[str, Tuple[str, str]]]]]
        ] = [],
        only_first=False,
        extra_fields: List[Any] = [],
    ) -> List[Any]:
        """
        Retrieves records matching multiple key-value pairs with optional query options,
        including filtering by nested relationships.

        Supports:
        - Simple equality (`field=value`)
        - `IS NOT NULL` (`field__isnot=True`)
        - `IS NULL` (`field__isnull=True`)
        - `LIKE` queries (`field__like="pattern%"`)
        - `IN` queries (`field__in=[val1, val2]`)
        - Comparison filters (`field__gt`, `field__gte`, `field__lt`, `field__lte`)

        Args:
            db (AsyncSession): The database session.
            keys (Dict[str, Any]): Filtering conditions.
            sort_params (List[Tuple[str, Any]]): Sorting criteria.
            only_first (bool): If `True`, return only the first matching record.
            extra_fields (List[Any]): Additional query options such as `joinedload`.

        Returns:
            List[ModelType]: Matching database records.
        """
        statement = await self.get_by_multi_keys_(keys=keys, extra_fields=extra_fields)
        result = await db.execute(statement)

        if only_first:
            instance = result.scalars().first()
            if not instance:
                raise HTTPException(
                    status_code=status.HTTP_204_NO_CONTENT,
                    detail=f"Instance of model '{self.model.__name__}' with '{keys}' not found",
                )
            return instance

        instances = result.scalars().all()

        if not instances:
            raise HTTPException(
                status_code=status.HTTP_204_NO_CONTENT,
                detail=f"Instance of model '{self.model.__name__}' with '{keys}' not found",
            )

        # Sorting is **kept intact** from your original implementation
        instances = self.sort(instances, sort_params)

        return instances

    async def autocomplete_field(
        self,
        db: AsyncSession,
        field: str,
        query: str = "",
        limit: int = 5,
        sort_order: sorting_order = "asc",
    ) -> List[str]:
        """
        Search for distinct values in a specific field of the model.

        Args:
            db (AsyncSession): The database session.
            field (str): The field to search for distinct values.
            query (str): Optional query string to filter the results.
            limit (int): Maximum number of distinct values to return.
            sort_order (sorting_order): Sorting order for the distinct values.

        Returns:
            List[str]: List of distinct values for the specified field.
        """
        if sort_order not in ("asc", "desc"):
            raise ValueError("Invalid sort order. Use 'asc' or 'desc'.")

        # Ensure the field exists in the model
        if not hasattr(self.model, field):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Field '{field}' does not exist in the model.",
            )
            # raise NotFoundError(message=f"Field '{field}' does not exist in the model.")

        # Access the column from the model
        column_field = getattr(self.model, field)

        # Split the query into search terms
        search_terms = query.split()

        # Create filters using the search terms
        filters = [column_field.ilike(f"%{term}%") for term in search_terms]

        # Build the query
        stmt = (
            select(func.distinct(column_field))
            .where(or_(*filters))
            .order_by(asc(column_field) if sort_order == "asc" else desc(column_field))
            .limit(limit)
        )

        # Execute the query
        result = await db.execute(stmt)
        instances = result.scalars().all()

        if not instances:
            raise HTTPException(
                status_code=status.HTTP_204_NO_CONTENT,
                detail=f"No distinct values found for field '{field}'",
            )
            # raise NotFoundError(
            #     status_code=status.HTTP_204_NO_CONTENT,
            #     message=f"No distinct values found for field '{field}'",
            # )

        return instances

    async def create(
        self, db: AsyncSession, obj_in: CreateSchemaType, user: Optional[User] = None
    ) -> ModelType:
        """Create a new record."""
        obj_data = obj_in.model_dump(exclude_none=True, exclude_unset=True)

        new_instance = self.model(**obj_data)
        db.add(new_instance)

        try:
            await db.commit()
            await db.refresh(new_instance)
        except SQLAlchemyError as e:
            await db.rollback()
            raise DatabaseCommitError(message=e)

        return new_instance

    async def create_with_associations(
        self,
        db: AsyncSession,
        obj_in: CreateSchemaType,
        # user: User = None,
        association_fields: Dict[str, Tuple[Type[ModelType], str]],
    ) -> ModelType:
        # Create a copy of obj_in, excluding any association fields
        obj_in_data = obj_in.model_copy(
            deep=True, update={field: None for field in association_fields.keys()}
        )
        new_instance = await self.create(db, obj_in_data)

        # Handle each association field
        for field_name, (model, relationship_attr) in association_fields.items():
            ids = getattr(obj_in, field_name, None)
            if ids:
                # Fetch related instances by IDs
                stmt = select(model).where(model.id.in_(ids))
                result = await db.execute(stmt)
                related_instances = result.scalars().all()

                # Extend the specified relationship attribute on the new instance
                getattr(new_instance, relationship_attr).extend(related_instances)

        # Commit the associations
        try:
            await db.commit()
            await db.refresh(new_instance)
        except SQLAlchemyError as e:
            await db.rollback()
            raise DatabaseCommitError(message=e)

        return new_instance

    async def update(
        self,
        db: AsyncSession,
        id: Any,
        obj_in: UpdateSchemaType,
        exclude: Dict[str, Any] = {},
        exclude_none: bool = True,
        exclude_unset: bool = True,
        user: Optional[User] = None,
    ) -> ModelType:
        """Update a record by ID."""
        instance = await self.get(db, id)

        update_data = obj_in.model_dump(
            exclude=exclude, exclude_none=exclude_none, exclude_unset=exclude_unset
        )

        for field, value in update_data.items():
            setattr(instance, field, value)
        try:
            await db.commit()
            await db.refresh(instance)
        except SQLAlchemyError as e:
            await db.rollback()
            raise DatabaseCommitError(message=e)

        return instance

    async def update_with_associations(
        self,
        db: AsyncSession,
        id: Any,
        obj_in: UpdateSchemaType,
        # user: User = None,  # Replace `User` with the actual user type if necessary
        association_fields: Dict[
            str, Tuple[Type[ModelType], str]
        ],  # {"tag_ids": (Tag, "tags"), "indicator_ids": (Indicator, "indicators")}
        exclude_none: bool = True,
        exclude_unset: bool = True,
    ) -> Optional[ModelType]:

        # Create a copy of obj_in with association fields set to None
        obj_in_copy = obj_in.model_copy(
            deep=True, update={field: None for field in association_fields.keys()}
        )

        # Update the main instance with user-specific context fields
        instance = await self.update(
            db,
            id,
            obj_in_copy,
            exclude={field for field in association_fields.keys()},
            exclude_none=exclude_none,
            exclude_unset=exclude_unset,
        )

        # Update each association field
        for field_name, (model, relationship_attr) in association_fields.items():
            ids = getattr(obj_in, field_name, None)
            if ids is not None:
                # Fetch the related instances based on IDs
                stmt = select(model).where(model.id.in_(ids))
                result = await db.execute(stmt)
                related_instances = result.scalars().all()

                # Replace the current relationship with the new instances
                setattr(instance, relationship_attr, related_instances)

        # Commit the updates
        try:
            await db.commit()
            await db.refresh(instance)
        except SQLAlchemyError as e:
            await db.rollback()
            raise DatabaseCommitError(message=e)

        return instance

    async def delete(self, db: AsyncSession, id: Any) -> None:
        """Delete a record by ID."""
        instance = await self.get(db, id)
        try:
            await db.delete(instance)
            await db.commit()
        except SQLAlchemyError as e:
            await db.rollback()
            raise DatabaseCommitError(message=e)
